#include "Player.hpp"
#include "Monster.hpp"

int Player::attack(Monster& m) const {
    const int damage{ args.damage };
    m.reduceHealth(damage);
    return damage;
}
