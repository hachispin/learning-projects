#include "Monster.hpp"
#include "Player.hpp"
#include "Random.hpp"
#include <format>
#include <stdexcept>

int Monster::attack(Player& p) const {
    const int damage{ args.damage };
    p.reduce_health(damage);
    return damage;
}

CreatureArgs Monster::get_monster_type_args(Monster::Type type) {
    using enum Monster::Type;

    std::string name{};
    int health{};
    int damage{};
    int gold{};
    char symbol{};

    switch (type) {
    case (dragon):
        name = "dragon";
        symbol = 'D';
        health = 20;
        damage = 4;
        gold = 100;
        break;
    case (orc):
        name = "orc";
        symbol = 'o';
        health = 4;
        damage = 2;
        gold = 25;
        break;
    case (slime):
        name = "slime";
        symbol = 's';
        health = 1;
        damage = 1;
        gold = 10;
        break;

    default:
        throw std::logic_error(std::format(
            "Unimplemented enum passed to `Monster` constructor "
            "(value = {})",
            static_cast<int>(type)));
    }
    return CreatureArgs{ name, health, damage, gold, symbol };
}

Monster Monster::get_random_monster() {
    auto monsterType{
        static_cast<Monster::Type>(Random::get(0, Monster::numTypes - 1))
    };

    return Monster{ Monster::get_monster_type_args(monsterType) };
}
