#include "Monster.hpp"
#include "Player.hpp"
#include "Random.hpp"
#include <cctype>
#include <format>
#include <iostream>
#include <string_view>

namespace Messages {
    bool isVowel(char c) {
        switch (std::tolower(c)) {
        case 'a':
        case 'e':
        case 'i':
        case 'o':
        case 'u':
            return true;
        default:
            return false;
        }
    }

    std::string greet_player(const Player& p) {
        return std::format(
            "Welcome, {}.\n"
            "You have {} health and are carrying {} gold.",
            p.get_name(), p.get_health(), p.get_gold());
    }

    std::string encounter(const Monster& m) {
        // Not needed but I got annoyed by the grammer

        if (isVowel(m.get_name()[0])) {
            return std::format(                     // you can shorten
                "You have encountered an {} ({}).", // this with runtime
                m.get_name(), m.get_symbol());      // format but it
        } else {                                    // doesn't really matter
            return std::format(
                "You have encountered a {} ({}).",
                m.get_name(), m.get_symbol());
        }
    }
    // Example usage:
    //
    // `std::cout << Messages::playerAttack(p.attack(m), m) << '\n';`
    std::string player_attack(const Monster& m, int damage) {
        return std::format(
            "You hit the {} for {} damage",
            m.get_name(), damage);
    }

    std::string monster_attack(const Monster& m, int damage) {
        return std::format(
            "The {} hit you for {} damage",
            m.get_name(), damage);
    }

    std::string new_level(int level) {
        return std::format("You are now level {}.", level);
    }

    std::string monster_killed(const Monster& m) {
        return std::format("You killed the {}.", m.get_name());
    }

    std::string found_gold(int amount) {
        return std::format("You found {} gold.", amount);
    }

    std::string lose(const Player& p) {
        return std::format(
            "You died at level {} and with {} gold.\n"
            "Too bad you can't take it with you!",
            p.get_level(), p.get_gold());
    }

    constexpr std::string_view choices{ "[R]un or [F]ight: " };
    constexpr std::string_view runSuccess{ "You successfully fled." };
    constexpr std::string_view runFail{ "You failed to flee." };
}

void check_eof() {
    if (std::cin.fail() || std::cin.eof()) {
        std::cout << "EOF\n";
        std::exit(0);
    }
}

Choice get_player_choice() {
    while (true) {
        std::cout << Messages::choices;
        std::string input{};
        std::getline(std::cin, input);
        check_eof();

        if (input.size() != 1) {
            std::cout << "Input must be a single character. "
                      << "Enter the bracketed key to perform "
                      << "the corresponding action.\n";
            continue;
        }
        // Consider using a switch-case here and elsewhere
        // if more options are made in the future
        if (std::tolower(input[0]) == 'r')
            return Choice::run;
        if (std::tolower(input[0]) == 'f')
            return Choice::fight;
        std::cout << "Invalid option\n";
    }
}

// oh my god i can't recurse son 😭😭😭 this shit
// is a whole fuckin state machine that i wouldn't
// touch with a INT_MAX feet pole...
void handle_choice(Choice c, Player& p, Monster& m, bool extCall = false) {
    using namespace Messages;

    static bool persist{ true };

    if (extCall)        // `extCall` means function call was
        persist = true; // made externally, not by recursion

    if (!persist) return;

    if (c == Choice::run) { // 50% chance to escape
        if (Random::get(1, 2) == 1) {
            std::cout << monster_attack(m, m.attack(p)) << '\n'
                      << runFail << '\n';
            persist = true;
            handle_choice(get_player_choice(), p, m);
        } else {
            std::cout << runSuccess << '\n';
            persist = false;
            return;
        }
    }

    if (c == Choice::fight)
        std::cout << player_attack(m, p.attack(m)) << '\n';

    if (m.is_dead()) { // stop the encounter
        p.add_gold(m.get_gold());
        std::cout << monster_killed(m) << '\n'
                  << new_level(p.level_up()) << '\n'
                  << found_gold(m.get_gold()) << '\n';
        persist = false;
    } else { // monster attacks player
        std::cout << monster_attack(m, m.attack(p)) << '\n';

        if (p.is_dead()) { // if player dies after being attacked
            persist = false;
        } else {
            persist = true;
            handle_choice(get_player_choice(), p, m);
        }
    }
}

int main() {
    using namespace Messages;

    std::string name{};
    std::cout << "Enter your name: ";
    std::getline(std::cin, name);
    check_eof();

    Player p{ name };
    std::cout << greet_player(p) << '\n';

    while (!p.has_won() && !p.is_dead()) {
        Monster m{ Monster::get_random_monster() };
        std::cout << encounter(m) << '\n';
        handle_choice(get_player_choice(), p, m, true);
    }

    if (p.is_dead())
        std::cout << lose(p) << '\n';
    else
        std::cout << "you win? "
                  << "(author didn't specify what winning looks like)\n";
    return 0;
}
