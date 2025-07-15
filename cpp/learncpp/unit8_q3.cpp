/* Question #3

Implement a game of Hi-Lo.
First, your program should pick a random integer between 1 and 100.
The user is given 7 tries to guess the number.

If the user does not guess the correct number, the program should
tell them whether they guessed too high or too low.

If the user guesses the right number, the program should tell them
they won. If they run out of guesses, the program should tell them
they lost, and what the correct number is. At the end of the game,
the user should be asked if they want to play again.

If the user doesn’t enter ‘y’ or ‘n’, ask them again.

Make the minimum and maximum values and the number of guesses a configurable parameter.
For this quiz, assume the user enters a valid number.
*/

#include <format>
#include <iostream>
#include <random>
#include <string>
#include <string_view>

namespace hiloConfig {
    constexpr int maxTries{ 7 };     // default: 7
    constexpr int upperBound{ 100 }; // default: 100
    constexpr int lowerBound{ 1 };   // default: 1
}

namespace messages { // the "Guess#X: " message is in getGuess() because it's quite short
    const std::string gameRules{ std::format("Let's play a game. I'm thinking of a number between "
                                             "{} and {}. You have {} tries to guess what it is.",
                                             hiloConfig::lowerBound,
                                             hiloConfig::upperBound,
                                             hiloConfig::maxTries) };

    const std::string lose(int ans) {
        return std::format("Sorry, you lose. The correct number was {}.", ans);
    }

    // don't use this if the user is correct
    const std::string hint(int guess, int ans) {
        if (guess > ans)
            return "Your guess is too high.";
        else
            return "Your guess is too low.";
    }

    const std::string win{ "Correct! You win!" };
    const std::string playAgain{ "Would you like to play again (y/n)? " };
    const std::string bye{ "Thank you for playing." };
}

int randInt() {
    static std::mt19937 mt{ std::random_device{}() };
    std::uniform_int_distribution gen{ hiloConfig::lowerBound, hiloConfig::upperBound };

    return gen(mt);
}

void checkEOF() {
    if (!std::cin) {
        std::cout << "EOF\n";
        std::exit(0);
    }
}

bool isValidGuess(std::string input) {
    using namespace hiloConfig;

    int n{};      // these two are used to verify that whole input
    size_t idx{}; // is read and that it falls within bounds

    try {
        n = std::stoi(input, &idx);
    } catch (std::exception& e) {
        return false;
    }

    if (input.size() != idx || n > upperBound || n < lowerBound)
        return false;
    return true;
}

int getGuess(std::string_view prompt) {
    int guess{};
    std::string input{};

    while (true) {
        std::cout << prompt;
        std::getline(std::cin, input);
        checkEOF();

        if (isValidGuess(input))
            break;

        std::cout << "Invalid guess\n";
    }

    guess = std::stoi(input);
    return guess;
}

void doHiloRound() {
    using namespace hiloConfig;

    int ans{ randInt() };
    int guess{};

    std::cout << messages::gameRules << '\n';
    for (int i = 1; i <= maxTries; ++i) {
        guess = getGuess("Guess #" + std::to_string(i) + ": ");

        if (guess == ans) {
            std::cout << messages::win << '\n';
            return;
        } else
            std::cout << messages::hint(guess, ans) << '\n';
    }
    std::cout << messages::lose(ans) << '\n';
}

bool getPlayAgainResponse() {
    std::string response{};
    char option{};

    while (true) {
        std::cout << messages::playAgain << '\n';
        std::getline(std::cin, response);
        checkEOF();

        option = static_cast<char>(std::tolower(response[0]));

        if (response.size() > 1 || (option != 'y' && option != 'n'))
            std::cout << "Invalid option\n";
        else
            break;
    }
    if (option == 'y')
        return true;
    return false;
}

int main() {
    bool keepPlaying{ true };

    while (keepPlaying) {
        doHiloRound();
        keepPlaying = getPlayAgainResponse();
    }

    std::cout << messages::bye << '\n';
    return 0;
}
