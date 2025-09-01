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
    static constexpr std::array<std::string, 9> wordBank{
        "mystery", "broccoli", "account",  // A word is randomly chosen
        "almost", "spaghetti", "opinion",  // from here as the game's solution.
        "beautiful", "distance", "luggage" // More can be added if need-be.
    };
    std::set<char>    guesses{};
    std::string       completeWord{}; // e.g. "broccolli"
    std::string       builtWord{};    // e.g. "br_cc_lli"
    std::vector<char> wrongGuesses{};
    const int         baseAttempts{ 6 };
    int               attempts{ baseAttempts };
    bool              winState{ false };

    // Only expected to be used once, so re-seeding isn't too bad here
    std::string chooseWord() const {
        // These conversions aren't necessary but will throw warnings otherwise
        int maxIntIndex{ static_cast<int>(wordBank.size() - 1) };

        std::random_device            rd{};
        std::mt19937                  mt{ rd() };
        std::uniform_int_distribution dist{ 0, maxIntIndex };

        return wordBank[static_cast<size_t>(dist(mt))];
    }
    /* helper functions for `guessletter()` */

    // guaranteed to be a unique guess upstream
    bool isCorrectGuess(char letter) const {
        for (const auto& i : completeWord) {
            if (letter == i)
                return true;
        }
        return false;
    }
    void revealLetter(char letter) {
        for (size_t i{ 0 }; i < completeWord.size(); ++i) {
            if (completeWord[i] == letter)
                builtWord[i] = letter;
        }
    }
    void updateWinStatus() { winState = (builtWord == completeWord); }

  public:
    GameWord()
        : completeWord{ chooseWord() }
        , builtWord{ std::string(completeWord.size(), '_') } {
        assert(completeWord.size() == builtWord.size());
    }
    enum GuessStatus {
        alreadyGuessed,
        correct,
        incorrect,
    };

    // Returns a `std::string` describing the game's status:
    // "The word: {builtWord}   Wrong guesses: {}"
    std::string gameStatus() const {
        // remaining attempts are represented through pluses
        std::string pluses(
            static_cast<size_t>(baseAttempts) - wrongGuesses.size(),
            '+');

        auto v{ wrongGuesses };
        std::sort(v.begin(), v.end());
        std::string attemptsDisplay{ pluses };

        for (const auto& x : v) {
            attemptsDisplay += x;
        }

        return std::format(
            "The word: {}   Wrong guesses: {}",
            builtWord, attemptsDisplay);
    }

    GuessStatus guessLetter(char letter) {
        if (attempts <= 0) throw std::logic_error(
            "Attempted to make guess with no attempts left");

        if (guesses.contains(letter)) return alreadyGuessed;
        guesses.insert(letter);

        if (!isCorrectGuess(letter)) {
            wrongGuesses.push_back(letter);
            --attempts;
            return incorrect;
        }

        revealLetter(letter);
        updateWinStatus();
        return correct;
    }

    static char getGuess();
    auto        getAttempts() const { return attempts; }
    const auto& getWrongGuesses() const { return wrongGuesses; }
    const auto& getBuiltWord() const { return builtWord; }
    const auto& getCompleteWord() const { return completeWord; }
    auto        getWinState() const { return winState; }
};
namespace Messages {
    constexpr char intro[]{
        "Welcome to C++man (a variant of Hangman)\n"
        "To win: guess the word.  To lose: run out of pluses."
    };

    constexpr char letterPrompt[]{ "Enter your next letter: " };
    std::string    describeGuessStatus(GameWord::GuessStatus gs, char letter) {
        using enum GameWord::GuessStatus;

        switch (gs) {
        case alreadyGuessed:
            return "You already guessed that.  Try again.";
        case correct:
            return std::format("Yes, '{}' is in the word!", letter);
        case incorrect:
            return std::format("No, '{}' is not in the word!", letter);
        default:
            throw std::invalid_argument(std::format(
                "Unexpected `GameWord::GuessStatus` value (enum = {})",
                static_cast<int>(gs)));
        }
    }
}
// note that this doesn't check if input was already guessed
char GameWord::getGuess() {
    using namespace Messages;
    std::string input{};

    while (true) {
        std::cout << letterPrompt;
        std::getline(std::cin, input);

        if (std::cin.fail() || std::cin.eof()) {
            std::cout << "EOF\n";
            std::exit(0);
        }

        if (input.size() != 1 || !std::isalpha(input[0]))
            std::cout << "That wasn't a valid input.  Try again.\n";
        else
            break;
    }
    return static_cast<char>(std::tolower(input[0]));
}
int main() {
    using namespace Messages;

    GameWord gw{};
    std::cout << intro << "\n\n";

    while (gw.getAttempts() > 0 && !gw.getWinState()) {
        std::cout << gw.gameStatus() << '\n';

        auto guess{ GameWord::getGuess() };
        auto guessRes{ gw.guessLetter(guess) };

        std::cout << describeGuessStatus(guessRes, guess) << "\n\n";
    }

    std::cout << "You " << (gw.getWinState() ? "win!" : "lose!")
              << "  The word was: " << gw.getCompleteWord()
              << '\n';

    return 0;
}
