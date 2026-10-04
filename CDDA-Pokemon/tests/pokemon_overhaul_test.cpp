// Gameplay tests for the Pokémon Overhaul mod.
//
// Copy into the CDDA source tree's tests/ folder, rebuild cata_test and run:
//   ./tests/cata_test --mods=dda,pokemon_overhaul "[pokemon_overhaul]"
#include <string>
#include <vector>

#include "avatar.h"
#include "calendar.h"
#include "cata_scope_helpers.h"
#include "cata_catch.h"
#include "creature.h"
#include "damage.h"
#include "dialogue.h"
#include "effect_on_condition.h"
#include "game.h"
#include "global_vars.h"
#include "item.h"
#include "magic.h"
#include "map.h"
#include "map_helpers.h"
#include "monster.h"
#include "monstergenerator.h"
#include "mtype.h"
#include "input_context.h"
#include "npc.h"
#include "npctalk.h"
#include "player_helpers.h"
#include "talker.h"
#include "type_id.h"

static const efftype_id effect_pet( "pet" );
static const efftype_id effect_pkmn_fainted( "pkmn_fainted" );
static const efftype_id effect_pkmn_trained( "pkmn_trained" );

static void run_eoc( const std::string &id, Creature *alpha, Creature *beta )
{
    dialogue d( get_talker_for( alpha ), beta ? get_talker_for( beta ) : nullptr );
    effect_on_condition_id( id )->activate( d );
}

static double mon_var( const monster &m, const std::string &key )
{
    const diag_value *v = m.maybe_get_value( key );
    return v ? v->dbl() : -1.0;
}

static monster &spawn_friendly( const std::string &id, const tripoint_bub_ms &where, int level )
{
    monster &m = spawn_test_monster( id, where );
    m.friendly = -1;
    m.add_effect( effect_pet, 1_turns, true );
    m.set_value( "pkmn_level", diag_value( static_cast<double>( level ) ) );
    m.set_value( "pkmn_xp", diag_value( 0.0 ) );
    return m;
}

static bool call_attack( monster &m, const std::string &attack )
{
    const auto it = m.type->special_attacks.find( attack );
    REQUIRE( it != m.type->special_attacks.end() );
    return it->second->call( m );
}

TEST_CASE( "pokemon_all_151_exist", "[pokemon_overhaul]" )
{
    int count = 0;
    for( const mtype &t : MonsterGenerator::generator().get_all_mtypes() ) {
        if( t.in_species( species_id( "POKEMON" ) ) &&
            !t.in_species( species_id( "PKMN_TRAINER_OWNED" ) ) ) {
            count++;
        }
    }
    CHECK( count == 151 );
}

TEST_CASE( "pokemon_capture", "[pokemon_overhaul]" )
{
    clear_avatar();
    clear_map();
    avatar &u = get_avatar();
    const tripoint_bub_ms near = u.pos_bub() + tripoint::east * 2;

    SECTION( "master ball always catches a wild Pokemon" ) {
        monster &pidgey = spawn_test_monster( "pkmn_pidgey", near );
        REQUIRE( pidgey.friendly == 0 );
        run_eoc( "EOC_PKMN_CAPTURE_MASTER", &pidgey, &u );
        CHECK( pidgey.friendly != 0 );
        CHECK( pidgey.has_effect( effect_pet ) );
        CHECK( pidgey.has_effect( effect_pkmn_trained ) );
        // The test avatar has no pockets, so the ball may land at their feet.
        bool got_ball = u.has_amount( itype_id( "pkmn_ball_registered" ), 1 );
        for( const item &it : get_map().i_at( u.pos_bub() ) ) {
            got_ball |= it.typeId() == itype_id( "pkmn_ball_registered" );
        }
        CHECK( got_ball );
    }
    SECTION( "a weakened Pokemon is far easier to catch than a healthy one" ) {
        int healthy = 0;
        int weak = 0;
        for( int i = 0; i < 200; i++ ) {
            clear_map();
            monster &a = spawn_test_monster( "pkmn_bulbasaur", near );
            run_eoc( "EOC_PKMN_CAPTURE_POKE", &a, &u );
            healthy += a.friendly != 0;
            clear_map();
            monster &b = spawn_test_monster( "pkmn_bulbasaur", near );
            b.set_hp( 1 );
            run_eoc( "EOC_PKMN_CAPTURE_POKE", &b, &u );
            weak += b.friendly != 0;
        }
        CAPTURE( healthy, weak );
        CHECK( healthy > 2 );
        CHECK( weak > healthy * 2 );
    }
    SECTION( "trainer Pokemon cannot be caught" ) {
        monster &onix = spawn_test_monster( "pkmn_onix_trainer", near );
        run_eoc( "EOC_PKMN_CAPTURE_MASTER", &onix, &u );
        CHECK( onix.friendly == 0 );
    }
}

TEST_CASE( "pokemon_wild_level_and_pokedex", "[pokemon_overhaul]" )
{
    clear_avatar();
    clear_map();
    get_globals().clear_global_values();
    const tripoint_bub_ms near = get_avatar().pos_bub() + tripoint::east * 2;

    monster &wild = spawn_test_monster( "pkmn_rattata", near );
    CHECK( mon_var( wild, "pkmn_level" ) < 0 );
    CHECK( call_attack( wild, "pkmn_init" ) );
    CHECK( mon_var( wild, "pkmn_level" ) >= 2 );
    CHECK( mon_var( wild, "pkmn_level" ) <= 7 );
    // Wild Pokémon never register in the Pokédex.
    CHECK_FALSE( call_attack( wild, "pkmn_register" ) );

    monster &mine = spawn_friendly( "pkmn_rattata", near + tripoint::south * 2, 5 );
    CHECK( call_attack( mine, "pkmn_register" ) );
    CHECK( get_globals().get_global_value( "pkmn_dex_rattata" ).dbl() == 1 );
    CHECK( get_globals().get_global_value( "pkmn_dex_count" ).dbl() == 1 );
    // Registering again does nothing.
    CHECK_FALSE( call_attack( mine, "pkmn_register" ) );
}

TEST_CASE( "pokemon_experience_and_level_up", "[pokemon_overhaul]" )
{
    clear_avatar();
    clear_map();
    const tripoint_bub_ms near = get_avatar().pos_bub() + tripoint::east * 2;
    monster &charmander = spawn_friendly( "pkmn_charmander", near, 5 );
    monster &zombie = spawn_test_monster( "mon_zombie", near + tripoint::east );

    zombie.apply_damage( &charmander, bodypart_id( "torso" ), 30 );
    CHECK( mon_var( charmander, "pkmn_xp" ) + ( mon_var( charmander, "pkmn_level" ) - 5 ) * 45 >= 30 );
    zombie.apply_damage( &charmander, bodypart_id( "torso" ), 1000 );
    CHECK( mon_var( charmander, "pkmn_level" ) > 5 );
    CHECK( charmander.get_effect_int( effect_pkmn_trained ) == mon_var( charmander, "pkmn_level" ) );

    SECTION( "Rare Candy raises the level by one" ) {
        const double before = mon_var( charmander, "pkmn_level" );
        run_eoc( "EOC_PKMN_USE_RARE_CANDY", &charmander, &get_avatar() );
        CHECK( mon_var( charmander, "pkmn_level" ) == before + 1 );
    }
}

TEST_CASE( "pokemon_evolution", "[pokemon_overhaul]" )
{
    clear_avatar();
    clear_map();
    const tripoint_bub_ms near = get_avatar().pos_bub() + tripoint::east * 2;

    SECTION( "level evolution" ) {
        monster &low = spawn_friendly( "pkmn_charmander", near, 10 );
        CHECK_FALSE( call_attack( low, "pkmn_evolve_0" ) );
        CHECK( low.type->id == mtype_id( "pkmn_charmander" ) );

        monster &high = spawn_friendly( "pkmn_charmander", near + tripoint::south * 2, 16 );
        CHECK( call_attack( high, "pkmn_evolve_0" ) );
        CHECK( high.type->id == mtype_id( "pkmn_charmeleon" ) );
        CHECK( high.friendly != 0 );
        CHECK( mon_var( high, "pkmn_level" ) == 16 );
    }
    SECTION( "wild Pokemon do not evolve" ) {
        monster &wild = spawn_test_monster( "pkmn_charmander", near );
        wild.set_value( "pkmn_level", diag_value( 40.0 ) );
        CHECK_FALSE( call_attack( wild, "pkmn_evolve_0" ) );
    }
    SECTION( "stone evolution picks the right Eeveelution" ) {
        monster &eevee = spawn_friendly( "pkmn_eevee", near, 20 );
        run_eoc( "EOC_PKMN_STONE_THUNDER", &eevee, &get_avatar() );
        CHECK_FALSE( call_attack( eevee, "pkmn_evolve_0" ) );
        CHECK( call_attack( eevee, "pkmn_evolve_1" ) );
        CHECK( eevee.type->id == mtype_id( "pkmn_jolteon" ) );
        CHECK( mon_var( eevee, "pkmn_stone_thunder" ) == 0 );
    }
    SECTION( "link cable evolution" ) {
        monster &kadabra = spawn_friendly( "pkmn_kadabra", near, 20 );
        run_eoc( "EOC_PKMN_STONE_LINK", &kadabra, &get_avatar() );
        CHECK( call_attack( kadabra, "pkmn_evolve_0" ) );
        CHECK( kadabra.type->id == mtype_id( "pkmn_alakazam" ) );
    }
}

static int damage_taken( const std::string &target, const std::string &dtype, int amount )
{
    clear_map();
    const tripoint_bub_ms near = get_avatar().pos_bub() + tripoint::east * 2;
    monster &attacker = spawn_friendly( "pkmn_mew", near, 50 );
    monster &victim = spawn_test_monster( target, near + tripoint::east );
    victim.set_hp( 300 );
    const int before = victim.get_hp();
    victim.deal_damage( &attacker, bodypart_id( "torso" ),
                        damage_instance( damage_type_id( dtype ), amount ) );
    return before - victim.get_hp();
}

TEST_CASE( "pokemon_type_chart", "[pokemon_overhaul]" )
{
    clear_avatar();
    // Water and Normal both resolve against bash armor, so they are directly comparable.
    const int neutral = damage_taken( "pkmn_charmander", "pkmn_normal", 30 );
    const int super = damage_taken( "pkmn_charmander", "pkmn_water", 30 );
    CAPTURE( neutral, super );
    REQUIRE( neutral > 0 );
    CHECK( super == 2 * neutral );

    // Fighting vs. Normal is super effective; vs. Ghost it does nothing.
    CHECK( damage_taken( "pkmn_gastly", "pkmn_fighting", 30 ) == 0 );
    // Electric vs. Ground: immune.
    CHECK( damage_taken( "pkmn_diglett", "pkmn_electric", 30 ) == 0 );
    // Ice vs. Dragon/Flying is 4x (neither target has cold armor).
    const int ice_neutral = damage_taken( "pkmn_snorlax", "pkmn_ice", 30 );
    const int ice_dragonite = damage_taken( "pkmn_dragonite", "pkmn_ice", 30 );
    CAPTURE( ice_neutral, ice_dragonite );
    CHECK( ice_dragonite == 4 * ice_neutral );
    const int fire_on_water = damage_taken( "pkmn_squirtle", "pkmn_fire", 40 );
    const int fire_neutral = damage_taken( "pkmn_squirtle", "pkmn_normal", 40 );
    CAPTURE( fire_on_water, fire_neutral );
    CHECK( fire_on_water < fire_neutral );
}

TEST_CASE( "pokemon_fainting", "[pokemon_overhaul]" )
{
    clear_avatar();
    clear_map();
    const tripoint_bub_ms near = get_avatar().pos_bub() + tripoint::east * 2;
    monster &pikachu = spawn_friendly( "pkmn_pikachu", near, 10 );
    monster &zombie = spawn_test_monster( "mon_zombie", near + tripoint::east );
    pikachu.apply_damage( &zombie, bodypart_id( "torso" ), 500 );
    CHECK_FALSE( pikachu.is_dead_state() );
    CHECK( pikachu.get_hp() == 1 );
    CHECK( pikachu.has_effect( effect_pkmn_fainted ) );

    SECTION( "a revive brings it back" ) {
        run_eoc( "EOC_PKMN_USE_REVIVE", &pikachu, &get_avatar() );
        CHECK_FALSE( pikachu.has_effect( effect_pkmn_fainted ) );
        CHECK( pikachu.get_hp() >= pikachu.get_hp_max() / 2 );
    }
    SECTION( "a second knockout is fatal" ) {
        pikachu.apply_damage( &zombie, bodypart_id( "torso" ), 500 );
        CHECK( pikachu.is_dead_state() );
    }
}

TEST_CASE( "pokemon_moves_scale_with_level", "[pokemon_overhaul]" )
{
    clear_avatar();
    clear_map();
    const tripoint_bub_ms near = get_avatar().pos_bub() + tripoint::east * 2;
    monster &low = spawn_friendly( "pkmn_charmander", near, 5 );
    monster &high = spawn_friendly( "pkmn_charmander", near + tripoint::south * 2, 60 );
    const spell ember = spell( spell_id( "pkmn_move_ember" ), 10 );
    CAPTURE( ember.damage( low ), ember.damage( high ) );
    CHECK( ember.damage( low ) > 0 );
    CHECK( ember.damage( high ) > ember.damage( low ) * 2 );
}

// ---------------------------------------------------------------------------
// Dialogue-driven systems
// ---------------------------------------------------------------------------
static bool pick_response( dialogue &d, const std::string &topic, const std::string &text_part )
{
    d.topic_stack.clear();
    d.add_topic( topic );
    d.gen_responses( d.topic_stack.back() );
    for( talk_response &r : d.responses ) {
        r.create_option_line( d, input_event() );
        if( r.text.find( text_part ) != std::string::npos ) {
            r.success.apply( d );
            return true;
        }
    }
    return false;
}

static bool has_response( dialogue &d, const std::string &topic, const std::string &text_part )
{
    d.topic_stack.clear();
    d.add_topic( topic );
    d.gen_responses( d.topic_stack.back() );
    for( talk_response &r : d.responses ) {
        r.create_option_line( d, input_event() );
        if( r.text.find( text_part ) != std::string::npos ) {
            return true;
        }
    }
    return false;
}

static std::vector<monster *> nearby( const std::string &id )
{
    std::vector<monster *> out;
    for( monster &m : g->all_monsters() ) {
        if( m.type->id == mtype_id( id ) && !m.is_dead() ) {
            out.push_back( &m );
        }
    }
    return out;
}

static bool has_item_nearby( const std::string &id )
{
    avatar &u = get_avatar();
    if( u.has_amount( itype_id( id ), 1 ) ) {
        return true;
    }
    for( const tripoint_bub_ms &p : get_map().points_in_radius( u.pos_bub(), 2 ) ) {
        for( const item &it : get_map().i_at( p ) ) {
            if( it.typeId() == itype_id( id ) ) {
                return true;
            }
        }
    }
    return false;
}

TEST_CASE( "pokemon_oak_gives_starter", "[pokemon_overhaul]" )
{
    clear_avatar();
    clear_map();
    get_globals().clear_global_values();
    avatar &u = get_avatar();
    npc &oak = spawn_npc( u.pos_bub().xy() + point::east * 3, "pkmn_npc_oak" );
    dialogue d( get_talker_for( u ), get_talker_for( oak ) );

    REQUIRE( has_response( d, "TALK_PKMN_OAK", "I'd like a Pokémon" ) );
    REQUIRE( pick_response( d, "TALK_PKMN_OAK_STARTER", "I choose Charmander" ) );
    std::vector<monster *> mine = nearby( "pkmn_charmander" );
    REQUIRE( mine.size() == 1 );
    CHECK( mine[0]->friendly != 0 );
    CHECK( mine[0]->has_effect( effect_pet ) );
    CHECK( mon_var( *mine[0], "pkmn_level" ) == 5 );
    CHECK( has_item_nearby( "pkmn_pokedex" ) );
    CHECK_FALSE( has_response( d, "TALK_PKMN_OAK", "I'd like a Pokémon" ) );
}

TEST_CASE( "pokemon_gym_battle", "[pokemon_overhaul]" )
{
    clear_avatar();
    clear_map();
    get_globals().clear_global_values();
    avatar &u = get_avatar();
    npc &brock = spawn_npc( u.pos_bub().xy() + point::east * 4, "pkmn_npc_brock" );
    npc &misty = spawn_npc( u.pos_bub().xy() + point::west * 4, "pkmn_npc_misty" );
    dialogue d( get_talker_for( u ), get_talker_for( brock ) );
    dialogue dm( get_talker_for( u ), get_talker_for( misty ) );

    // No Pokémon out: no challenge.
    CHECK_FALSE( has_response( d, "TALK_PKMN_BROCK", "I challenge you" ) );
    spawn_friendly( "pkmn_squirtle", u.pos_bub() + tripoint::south * 2, 20 );
    // Misty wants one badge first.
    CHECK_FALSE( has_response( dm, "TALK_PKMN_MISTY", "I challenge you" ) );

    REQUIRE( pick_response( d, "TALK_PKMN_BROCK", "I challenge you" ) );
    std::vector<monster *> geodude = nearby( "pkmn_geodude_trainer" );
    std::vector<monster *> onix = nearby( "pkmn_onix_trainer" );
    REQUIRE( geodude.size() == 1 );
    REQUIRE( onix.size() == 1 );
    CHECK( mon_var( *geodude[0], "pkmn_level" ) == 14 );
    CHECK( mon_var( *onix[0], "pkmn_level" ) == 16 );
    CHECK( has_response( d, "TALK_PKMN_BROCK", "still going" ) );
    CHECK_FALSE( has_response( d, "TALK_PKMN_BROCK", "I win" ) );

    geodude[0]->die( &get_map(), nullptr );
    onix[0]->die( &get_map(), nullptr );
    g->cleanup_dead();
    REQUIRE( pick_response( d, "TALK_PKMN_BROCK", "I win" ) );
    CHECK( has_item_nearby( "pkmn_badge_boulder" ) );
    CHECK( get_globals().get_global_value( "pkmn_badge_count" ).dbl() == 1 );
    CHECK( has_response( d, "TALK_PKMN_BROCK", "rematch" ) );
    // Now Misty will battle.
    CHECK( has_response( dm, "TALK_PKMN_MISTY", "I challenge you" ) );
}

TEST_CASE( "pokemon_center_heals", "[pokemon_overhaul]" )
{
    clear_avatar();
    clear_map();
    avatar &u = get_avatar();
    npc &joy = spawn_npc( u.pos_bub().xy() + point::east * 3, "pkmn_npc_nurse_joy" );
    monster &pikachu = spawn_friendly( "pkmn_pikachu", u.pos_bub() + tripoint::south * 2, 10 );
    monster &zombie = spawn_test_monster( "mon_zombie", u.pos_bub() + tripoint::south * 5 );
    pikachu.apply_damage( &zombie, bodypart_id( "torso" ), 500 );
    REQUIRE( pikachu.has_effect( effect_pkmn_fainted ) );
    dialogue d( get_talker_for( u ), get_talker_for( joy ) );
    REQUIRE( pick_response( d, "TALK_PKMN_JOY", "heal my Pokémon" ) );
    CHECK_FALSE( pikachu.has_effect( effect_pkmn_fainted ) );
    CHECK( pikachu.get_hp() == pikachu.get_hp_max() );
}

TEST_CASE( "pokemon_use_moves_in_battle", "[pokemon_overhaul]" )
{
    clear_avatar();
    clear_map();
    restore_on_out_of_scope restore_calendar_turn( calendar::turn );
    calendar::turn = daylight_time( calendar::turn ) + 2_hours;
    get_map().invalidate_map_cache( 0 );
    get_map().build_map_cache( 0, true );
    const tripoint_bub_ms near = get_avatar().pos_bub() + tripoint::east * 3;

    SECTION( "moves hit a hostile target and unlock with level" ) {
        monster &charmander = spawn_friendly( "pkmn_charmander", near, 40 );
        monster &zombie = spawn_test_monster( "mon_zombie", near + tripoint::east * 3 );
        const int before = zombie.get_hp();
        charmander.set_dest( zombie.pos_abs() );
        REQUIRE( charmander.attack_target() == &zombie );
        CHECK( call_attack( charmander, "pkmn_move_ember" ) );
        CHECK( call_attack( charmander, "pkmn_move_fire_blast" ) );
        CHECK( zombie.get_hp() < before );

        monster &weak = spawn_friendly( "pkmn_charmander", near + tripoint::south * 2, 5 );
        weak.set_dest( zombie.pos_abs() );
        CHECK_FALSE( call_attack( weak, "pkmn_move_fire_blast" ) );
    }
}
