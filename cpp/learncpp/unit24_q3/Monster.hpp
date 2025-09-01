#ifndef MONSTER_H
#define MONSTER_H

#include "Creature.hpp"

class Player;

class Monster : public Creature {
  public:
    static constexpr int numTypes{ 3 };
    enum class Type {
        dragon,
        orc,
        slime,
    };

    Monster(Monster::Type type)
        : Creature(getMonsterTypeArgs(type)) {}

    Monster(CreatureArgs args)
        : Creature(args) {}

    // Returns the damage applied to `p`
    int attack(Player& p) const; // forward declare

    static CreatureArgs getMonsterTypeArgs(Monster::Type type);
    static Monster      getRandomMonster();
};

#endif
