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

    std::string greetPlayer(const Player& p) {
        return std::format(
            "Welcome, {}.\n"
            "You have {} health and are carrying {} gold.",
            p.getName(), p.getHealth(), p.getGold());
    }

    std::string encounter(const Monster& m) {
        // Not needed but I got annoyed by the grammer

        if (isVowel(m.getName()[0])) {
            return std::format(                     // you can shorten
                "You have encountered an {} ({}).", // this with runtime
                m.getName(), m.getSymbol());        // format but it
        } else {                                    // doesn't really matter
            return std::format(
                "You have encountered a {} ({}).",
                m.getName(), m.getSymbol());
        }
    }
    // Example usage:
    //
    // `std::cout << Messages::playerAttack(p.attack(m), m) << '\n';`
    std::string playerAttack(const Monster& m, int damage) {
        return std::format(
            "You hit the {} for {} damage",
            m.getName(), damage);
    }

    std::string monsterAttack(const Monster& m, int damage) {
        return std::format(
            "The {} hit you for {} damage",
            m.getName(), damage);
    }

    std::string newLevel(int level) {
        return std::format("You are now level {}.", level);
    }

    std::string monsterKilled(const Monster& m) {
        return std::format("You killed the {}.", m.getName());
    }

    std::string foundGold(int amount) {
        return std::format("You found {} gold.", amount);
    }

    std::string lose(const Player& p) {
        return std::format(
            "You died at level {} and with {} gold.\n"
            "Too bad you can't take it with you!",
            p.getLevel(), p.getGold());
    }

    constexpr std::string_view choices{ "[R]un or [F]ight: " };
    constexpr std::string_view runSuccess{ "You successfully fled." };
    constexpr std::string_view runFail{ "You failed to flee." };
}

void checkEof() {
    if (std::cin.fail() || std::cin.eof()) {
        std::cout << "EOF\n";
        std::exit(0);
    }
}

Choice getPlayerChoice() {
    while (true) {
        std::cout << Messages::choices;
        std::string input{};
        std::getline(std::cin, input);
        checkEof();

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

// Uses recursion to continue until either the player:
// - has fled
// - has killed the monster
// - has been killed by the monster
void handleChoice(Choice c, Player& p, Monster& m) {
    using namespace Messages;

    static bool persist{ true };

    if (c == Choice::run) { // 50% chance to escape
        if (Random::get(1, 2) == 1) {
            std::cout << monsterAttack(m, m.attack(p)) << '\n'
                      << runFail << '\n';
            handleChoice(getPlayerChoice(), p, m);
        } else {
            std::cout << runSuccess << '\n';
            return;
        }
    }

    if (!persist) return;

    if (c == Choice::fight)
        std::cout << playerAttack(m, p.attack(m)) << '\n';

    if (m.isDead()) {
        p.addGold(m.getGold());
        std::cout << monsterKilled(m) << '\n'
                  << newLevel(p.levelUp()) << '\n'
                  << foundGold(m.getGold()) << '\n';
    } else {
        std::cout << monsterAttack(m, m.attack(p)) << '\n';
        if (p.isDead())
            return;
        handleChoice(getPlayerChoice(), p, m);
    }
    if (!persist) return;
}

int main() {
    using namespace Messages;

    std::string name{};
    std::cout << "Enter your name: ";
    std::getline(std::cin, name);
    checkEof();

    Player p{ name };
    std::cout << greetPlayer(p) << '\n';

    while (!p.hasWon() && !p.isDead()) {
        Monster m{ Monster::getRandomMonster() };
        std::cout << encounter(m) << '\n';
        handleChoice(getPlayerChoice(), p, m);
    }

    if (p.isDead())
        std::cout << lose(p) << '\n';
    else
        std::cout << "you win? "
                  << "(author didn't specify what winning looks like)\n";
    return 0;
}
