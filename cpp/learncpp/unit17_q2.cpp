#include <array>
#include <format>
#include <iostream>
#include <random>
#include <stdexcept>
#include <vector>

namespace rdm {
    std::random_device rd{};
    std::mt19937       mt{ rd() };

    int randRange(int start, int stop) {
        if (start > stop) throw std::invalid_argument(
            "Invalid range passed to `randRange`: "
            "`start` can't be greater than `stop`");

        std::uniform_int_distribution dist{ start, stop };
        return dist(mt);
    }
}

struct Potion {
    std::string name;
    int         cost;
};

class Player {
  private:
    std::string         name{};
    std::vector<Potion> inventory{};
    int                 gold{};

    static constexpr int lowestGold{ 75 };
    static constexpr int highestGold{ 125 };

  public:
    Player() = delete;

    Player(std::string name)
        : name{ name }
        , gold(rdm::randRange(lowestGold, highestGold)) {}

    bool canPurchase(Potion p) {
        return gold >= p.cost;
    }

    // The player's gold should've been checked prior to this so
    // it wont go into the negatives (unless you wanna add debt?)
    void purchaseItem(Potion p) {
        inventory.push_back(p);
        gold -= p.cost;
    }

    const auto& getName() const { return name; }
    const auto& getInventory() const { return inventory; }
    auto        getGold() const { return gold; }
};

void checkEof() {
    if (std::cin.fail() || std::cin.eof()) {
        std::cout << "EOF\n";
        std::exit(0);
    }
}

namespace Messages {
    using sv = std::string_view;

    constexpr sv welcome{ "Welcome to Roscoe's potion emporium!" };
    constexpr sv goodbye{ "Thanks for shopping at Roscoe's potion emporium!" };
    constexpr sv shopWelcome{ "Here is our selection for today:" };
    constexpr sv invalidInput{ "That is an invalid input.  Try again: " };
    constexpr sv cantPurchase{ "You can not afford that." };
    constexpr sv namePrompt{ "Enter your name: " };
    constexpr sv potionPrompt{
        "Enter the number of the potion you'd like to buy, or 'q' to quit: "
    };

    std::string purchase(Potion p, int gold) {
        return std::format(
            "You purchased a potion of {}.  You have {} gold left.",
            p.name, gold);
    }

    std::string playerWelcome(Player p) {
        return std::format(
            "Hello, {}, you have {} gold.",
            p.getName(), p.getGold());
    }
}

namespace Shop {
    constexpr int numPotions{ 4 };

    constexpr std::array<const Potion, numPotions> potions{
        {
         { "healing", 20 },
         { "mana", 30 },
         { "speed", 12 },
         { "invisibility", 50 },
         }
    };

    void display() {
        for (size_t i{ 0 }; i < numPotions; ++i) {
            const auto& p{ potions[i] };
            std::cout << i + 1 << ") " << p.name << " costs " << p.cost << '\n';
        }
    }

    bool isValidOption(const std::string& input) {
        int index{}; // the one-indexed choice from the user
        try {
            index = (std::stoi(input));
        } catch (...) {   // consider replacing with
            return false; // explicit catches?
        }
        return index > 0 && index <= numPotions;
    }

    // if `std::nullopt` is returned, the user has quit (with 'q').
    // note that the returned `size_t` is one-indexed
    std::optional<size_t> getOption() {
        std::string option{};
        std::cout << Messages::potionPrompt;

        while (true) {
            std::getline(std::cin, option);
            checkEof();

            if (option == "q" || option == "Q")
                return std::nullopt;

            if (!isValidOption(option))
                std::cout << Messages::invalidInput;
            else
                break;
        }
        return static_cast<size_t>(std::stoi(option));
    }
}

int main() {
    std::cout << Messages::welcome << '\n';

    std::string name{};
    std::cout << Messages::namePrompt;
    std::getline(std::cin, name);
    checkEof();

    Player user{ name };
    std::cout << Messages::playerWelcome(user) << '\n';

    while (true) { // shop loop
        std::cout << '\n';
        std::cout << Messages::shopWelcome << '\n';
        Shop::display();

        auto potionIndex{ Shop::getOption() };
        if (!potionIndex) break;

        auto potion{ Shop::potions[*potionIndex - 1] };
        if (user.canPurchase(potion)) {
            user.purchaseItem(potion);
            std::cout << Messages::purchase(potion, user.getGold()) << '\n';
        } else {
            std::cout << Messages::cantPurchase << '\n';
        }
    }

    std::cout << Messages::goodbye << '\n';

    return 0;
}
