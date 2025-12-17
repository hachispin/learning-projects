#include <algorithm>
#include <array>
#include <cassert>
#include <format>
#include <iostream>
#include <random>
#include <set>
#include <stdexcept>
#include <string>
#include <vector>

class GameWord {
  private:
    static constexpr std::array<std::string, 9> word_bank{
        "mystery", "broccoli", "account",  // A word is randomly chosen
        "almost", "spaghetti", "opinion",  // from here as the game's solution.
        "beautiful", "distance", "luggage" // More can be added if need-be.
    };

    std::set<char> guesses{};
    std::string complete_word{}; // e.g. "broccolli"
    std::string built_word{};    // e.g. "br_cc_lli"
    std::vector<char> wrong_guesses{};
    const int base_attempts{ 6 };
    int attempts{ base_attempts };
    bool win_state{ false };

    // Only expected to be used once, so re-seeding isn't too bad here
    std::string choose_word() const {
        // These conversions aren't necessary but will throw warnings otherwise
        auto max_int_index{ static_cast<int>(word_bank.size() - 1) };

        std::random_device rd{};
        std::mt19937 mt{ rd() };
        std::uniform_int_distribution dist{ 0, max_int_index };

        return word_bank[static_cast<size_t>(dist(mt))];
    }
    /* helper functions for `guessletter()` */

    // guaranteed to be a unique guess upstream
    bool is_correct_guess(char letter) const {
        for (const auto& i : complete_word) {
            if (letter == i) {
                return true;
            }
        }
        
        return false;
    }

    void reveal_letter(char letter) {
        for (size_t i{ 0 }; i < complete_word.size(); ++i) {
            if (complete_word[i] == letter) {
                built_word[i] = letter;
            }
        }
    }

    void update_win_status() { win_state = (built_word == complete_word); }

  public:
    GameWord()
        : complete_word{ choose_word() }
        , built_word{ std::string(complete_word.size(), '_') } {
        assert(complete_word.size() == built_word.size());
    }

    enum GuessStatus {
        AlreadyGuessed,
        Correct,
        Incorrect,
    };

    // Returns a `std::string` describing the game's status:
    // "The word: {builtWord}   Wrong guesses: {}"
    std::string game_status() const {
        // remaining attempts are represented through pluses
        auto num_pluses = static_cast<size_t>(base_attempts) - wrong_guesses.size();
        std::string pluses(num_pluses, '+');

        auto v{ wrong_guesses };
        std::sort(v.begin(), v.end());
        std::string attempts_display{ pluses };

        for (const auto& x : v) {
            attempts_display += x;
        }

        return std::format(
            "The word: {}   Wrong guesses: {}",
            built_word, attempts_display);
    }

    GuessStatus guess_letter(char letter) {
        if (attempts <= 0) {
            throw std::logic_error(
                "Attempted to make guess with no attempts left");
        }

        if (guesses.contains(letter)) {
            return AlreadyGuessed;
        }

        guesses.insert(letter);

        if (!is_correct_guess(letter)) {
            wrong_guesses.push_back(letter);
            --attempts;
            return Incorrect;
        }

        reveal_letter(letter);
        update_win_status();
        return Correct;
    }

    static char get_guess();
    auto get_attempts() const { return attempts; }
    const auto& get_wrong_guesses() const { return wrong_guesses; }
    const auto& get_built_word() const { return built_word; }
    const auto& get_complete_word() const { return complete_word; }
    auto get_win_state() const { return win_state; }
};

namespace Messages {
    constexpr char intro[]{
        "Welcome to C++man (a variant of Hangman)\n"
        "To win: guess the word.  To lose: run out of pluses."
    };

    constexpr char letter_prompt[]{ "Enter your next letter: " };
    std::string describe_guess_status(GameWord::GuessStatus gs, char letter) {
        using enum GameWord::GuessStatus;

        switch (gs) {
        case AlreadyGuessed:
            return "You already guessed that.  Try again.";
        case Correct:
            return std::format("Yes, '{}' is in the word!", letter);
        case Incorrect:
            return std::format("No, '{}' is not in the word!", letter);

        default:
            throw std::invalid_argument(std::format(
                "Unexpected `GameWord::GuessStatus` value (enum = {})",
                static_cast<int>(gs)));
        }
    }
}
// note that this doesn't check if input was already guessed
char GameWord::get_guess() {
    using namespace Messages;
    std::string input{};

    while (true) {
        std::cout << letter_prompt;
        std::getline(std::cin, input);

        if (std::cin.fail() || std::cin.eof()) {
            std::cout << "EOF\n";
            std::exit(0);
        }

        if (input.size() != 1 || !std::isalpha(input[0])) {
            std::cout << "That wasn't a valid input.  Try again.\n";
        } else {
            break;
        }
    }

    return static_cast<char>(std::tolower(input[0]));
}

int main() {
    using namespace Messages;

    GameWord gw{};
    std::cout << intro << "\n\n";

    while (gw.get_attempts() > 0 && !gw.get_win_state()) {
        std::cout << gw.game_status() << '\n';

        auto guess{ GameWord::get_guess() };
        auto guess_res{ gw.guess_letter(guess) };

        std::cout << describe_guess_status(guess_res, guess) << "\n\n";
    }

    std::cout << "You " << (gw.get_win_state() ? "win!" : "lose!")
              << "  The word was: " << gw.get_complete_word()
              << '\n';

    return 0;
}
