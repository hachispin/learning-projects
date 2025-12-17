#ifndef CREATURE_H
#define CREATURE_H

#include <string>

struct CreatureArgs {
    std::string name{};
    int health{};
    int damage{};
    int gold{};
    char symbol{};
};

class Creature {
  protected:
    CreatureArgs args{};

  public:
    Creature(const std::string& name, int health, int damage, int gold, char symbol)
        : args{ name, health, damage, gold, symbol } {}

    Creature(const CreatureArgs& args)
        : args{ args } {}

    void add_gold(int amount) { args.gold += amount; }
    void reduce_health(int amount) { args.health -= amount; }

    bool is_dead() const { return args.health <= 0; }

    const auto& get_name() const { return args.name; }
    auto get_health() const { return args.health; }
    auto get_damage() const { return args.damage; }
    auto get_gold() const { return args.gold; }
    auto get_symbol() const { return args.symbol; }
};

#endif
