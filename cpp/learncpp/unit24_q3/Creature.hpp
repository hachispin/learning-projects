#ifndef CREATURE_H
#define CREATURE_H

#include <string>

struct CreatureArgs {
    std::string name{};
    int         health{};
    int         damage{};
    int         gold{};
    char        symbol{};
};

class Creature {
  protected:
    CreatureArgs args{};

  public:
    Creature(const std::string& name, int health, int damage, int gold, char symbol)
        : args{ name, health, damage, gold, symbol } {}

    Creature(const CreatureArgs& args)
        : args{ args } {}

    void addGold(int amount) { args.gold += amount; }
    void reduceHealth(int amount) { args.health -= amount; }

    bool isDead() const { return args.health <= 0; }

    const auto& getName() const { return args.name; }
    auto        getHealth() const { return args.health; }
    auto        getDamage() const { return args.damage; }
    auto        getGold() const { return args.gold; }
    auto        getSymbol() const { return args.symbol; }
};

#endif
