#ifndef PLAYER_H
#define PLAYER_H

#include "Creature.hpp"

class Monster;

enum class Choice {
    run,
    fight,
};

class Player : public Creature {
  private:
    int level{};

  public:
    Player() = delete;
    Player(const std::string& name)
        : Creature(name, 10, 1, 0, '@')
        , level{ 1 } {}

    // Returns the level that the `Player` has upgraded to
    int levelUp() {
        ++args.damage;
        return ++level;
    }
    // Returns the damage applied to `m`
    int attack(Monster& m) const; // forward declare

    auto getLevel() const { return level; }
    bool hasWon() const { return level >= 20; }
};

#endif
