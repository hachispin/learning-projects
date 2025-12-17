#include <array>
#include <format>
#include <iostream>
#include <random>
#include <stdexcept>
#include <vector>

namespace rdm {
    std::random_device rd{};
    std::mt19937 mt{ rd() };

    int rand_range(int start, int stop) {
        if (start > stop) {
            throw std::invalid_argument(std::format(
                "{}(): invalid range, start={} can't be greater than stop={}",
                __func__, start, stop));
        }

        std::uniform_int_distribution dist{ start, stop };
        return dist(mt);
    }
}

struct Potion {
    std::string name{};
    int cost{};
};

class Player {
  private:
    std::string name{};
    std::vector<Potion> inventory{};
    int gold{};

    static constexpr int lowest_gold{ 75 };
    static constexpr int highest_gold{ 125 };

  public:
    Player() = delete;

    Player(std::string name)
        : name{ name }
        , gold(rdm::rand_range(lowest_gold, highest_gold)) {}

    /// Purchases `p` unless `p.cost > gold`, throwing `std::invalid_argument`.
    void purchase_item(const Potion& p) {
        if (p.cost > gold) {
            throw std::invalid_argument(std::format(
                "{}(): Attempted to purchase potion with cost={} with gold={} (not enough gold)",
                __func__, p.cost, gold));
        }

        inventory.push_back(p);
        gold -= p.cost;
    }

    const auto& get_name() const { return name; }
    const auto& get_inventory() const { return inventory; }
    auto get_gold() const { return gold; }
};

/// Checks if `std::cin` fail-bit is set. If so, exit the program.
void check_eof() {
    if (std::cin.fail() || std::cin.eof()) {
        std::cout << "EOF\n";
        std::exit(0);
    }
}

/// Just a bunch of strings. For i18n I guess?
namespace Messages {
    using sv = std::string_view;

    constexpr sv welcome{ "Welcome to Roscoe's potion emporium!" };
    constexpr sv goodbye{ "Thanks for shopping at Roscoe's potion emporium!" };
    constexpr sv shop_welcome{ "Here is our selection for today:" };
    constexpr sv invalid_input{ "That is an invalid input. Try again: " };
    constexpr sv cant_purchase{ "You can not afford that." };
    constexpr sv name_prompt{ "Enter your name: " };
    constexpr sv potion_prompt{
        "Enter the number of the potion you'd like to buy, or 'q' to quit: "
    };

    std::string purchase(const Potion& p, int gold) {
        return std::format(
            "You purchased a potion of {}. You have {} gold left.",
            p.name, gold);
    }

    std::string player_welcome(const Player& p) {
        return std::format(
            "Hello, {}, you have {} gold.",
            p.get_name(), p.get_gold());
    }
}

/// I think I could've made this a namespace...
class Shop {
  private:
    static constexpr int numPotions{ 4 };
    static constexpr std::array<Potion, numPotions> potions{
        {
         { "healing", 20 },
         { "mana", 30 },
         { "speed", 12 },
         { "invisibility", 50 },
         }
    };

  public:
    /// Displays the shop's items.
    void display(std::ostream& out) const {
        for (size_t i{ 0 }; i < numPotions; ++i) {
            const auto& p{ potions[i] };
            out << i + 1 << ") " << p.name << " costs " << p.cost << '\n';
        }
    }

    /// Helper for `get_option()`.
    bool is_valid_option(const std::string& input) const {
        int index{}; // the one-indexed choice from the user

        try {
            index = std::stoi(input);
        } catch (...) {   // consider replacing with
            return false; // explicit catches?
        }

        return index > 0 && index <= numPotions;
    }

    /// If `std::nullopt` is returned, the user has quit (with 'q').
    ///
    /// Note that the returned potion index is already zero-indexed.
    std::optional<size_t> get_option(std::ostream& out) const {
        std::string option{};
        out << Messages::potion_prompt;

        while (true) {
            std::getline(std::cin, option);
            check_eof();

            if (option == "q" || option == "Q") {
                return std::nullopt;
            }

            if (!is_valid_option(option)) {
                out << Messages::invalid_input;
            } else {
                break;
            }
        }

        return static_cast<size_t>(std::stoi(option)) - 1;
    }

    /// Throws `std::invalid_argument` if 
    /// `potion_index` is out-of-bounds.
    Potion get_potion(size_t potion_index) {
        if (potion_index >= potions.size()) {
            throw std::invalid_argument(std::format(
                "{}(): invalid potion_index={} is greater than potions.size={}",
                __func__, potion_index, potions.size()));
        }

        return potions[potion_index];
    }
};

int main() {
    std::cout << Messages::welcome << '\n';

    std::string name{};
    std::cout << Messages::name_prompt;
    std::getline(std::cin, name);
    check_eof();

    Player user{ name };
    Shop shop{};
    std::cout << Messages::player_welcome(user) << '\n';

    while (true) { // shop loop
        std::cout << Messages::shop_welcome << '\n';
        shop.display(std::cout);
        std::cout << '\n';

        auto potion_index{ shop.get_option(std::cout) };

        // User has exited the shop.
        if (!potion_index) {
            break;
        }

        auto potion{ shop.get_potion(*potion_index) };

        try {
            user.purchase_item(potion);
            std::cout << Messages::purchase(potion, user.get_gold()) << '\n';
        } catch (const std::invalid_argument& e) {
            std::cout << Messages::cant_purchase << '\n';
        }
    }

    std::cout << Messages::goodbye << '\n';

    return 0;
}
