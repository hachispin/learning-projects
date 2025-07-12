#include <cmath>
#include <format>
#include <iostream>
#include <stdexcept>
#include <string>
#include <tuple>

std::string removeAllSpaces(std::string s) {
    for (size_t i = 0; i < s.size(); i++) {
        if (s[i] == ' ') {
            s.erase(i, 1);
            i--;
        }
    }
    return s;
}
// allowed operators are also defined here
bool isOperator(char chr) {
    switch (chr) {
    case '+':
    case '-':
    case '*':
    case '/':
    case '^': // exponentiation
        return true;
    default:
        return false;
    }
}

size_t findOperatorIndex(std::string_view expr) {
    auto opIdx = std::string::npos;
    for (size_t i = 0; i < expr.size(); i++) {
        if (isOperator(expr[i])) {
            opIdx = i; // only finds first operator as intended
            break;
        }
    }
    return opIdx;
}

std::tuple<std::string, std::string> // ordered (left, right) of index
splitByIndex(std::string_view sv, size_t idx) {
    if (idx > sv.size() - 1) {
        std::string msg{ std::format("Provided index '{}' is outside string in splitByIndex()",
                                     idx) };
        throw std::out_of_range(msg);
    }

    // doesn't include the char (operator) at the splitting index `idx`
    return { std::string(sv.substr(0, idx)), std::string(sv.substr(idx + 1)) };
}

// must have:
//      no unnecessary leading zeroes
//      only numbers and up to one dot
//      size greater than 1 (i.e. not blank)
bool isValidNumber(std::string_view s) {
    if (s.size() == 0)
        return false;
    if (s[0] == '.' || s.back() == '.')             // number can't start or end with '.'
        return false;                               // ^^ this also doesnt allow shorthand ".5"
    if (s[0] == '0' && s.size() > 1 && s[1] != '.') // only allow a leading zero if next char is '.'
        return false;

    int dotCount = 0;
    for (char chr : s) {
        if (chr <= '9' && chr >= '0')
            continue;
        if (chr == '.')
            dotCount += 1;
        else
            return false;
    }

    if (dotCount <= 1)
        return true;
    else
        return false;
}

// for simplicity, a valid expression here is defined as
// one operator between two (valid) numeric substrings
bool isValidExpression(std::string_view expr) {
    size_t opIdx{ findOperatorIndex(expr) };

    if (expr.size() < 3)
        return false;
    if (opIdx == std::string::npos)
        return false;

    auto [left, right] = splitByIndex(expr, opIdx);

    if (!isValidNumber(left) || !isValidNumber(right))
        return false;
    return true;
}

// takes inputs in the format:
// a?b, where ? is a defined operator
// e.g. a+b
double doOperation(std::string_view expr) {
    // all of this is done assuming valid expr!
    size_t opIdx{ findOperatorIndex(expr) };
    auto [left, right] = splitByIndex(expr, opIdx);
    double leftDouble = std::stod(left);
    double rightDouble = std::stod(right);

    switch (expr[opIdx]) { // i.e. the operator
    case '+':
        return leftDouble + rightDouble;
    case '-':
        return leftDouble - rightDouble;
    case '*':
        return leftDouble * rightDouble;
    case '/':
        if (rightDouble == 0.0)
            throw std::runtime_error("Division by zero"); // throw because this should've been
        return leftDouble / rightDouble;                  // handled prior to reaching this point
    case '^':
        return std::pow(leftDouble, rightDouble);
    default:
        std::string msg{ std::format("Invalid operator '{}' given by findOperatorIndex()",
                                     expr[opIdx]) };
        throw std::logic_error(msg);
    }
}

int main() {
    std::string input{};

    while (true) {
        std::cout << "Calculate something: ";
        std::getline(std::cin, input);
        input = removeAllSpaces(input);

        if (!isValidExpression(input)) {
            std::cout << "Invalid expression\n";
            continue;
        } else {
            size_t opIdx = findOperatorIndex(input);
            auto [left, right] = splitByIndex(input, opIdx);

            // division by zero
            if (input[opIdx] == '/' && std::stod(right) == 0.0) {
                std::cout << "You cannot divide by zero!\n";
                continue;
            }
        }
        break;
    }
    // TODO: trim spaces less aggresively because
    // 1 2 3 4 * 5
    // is interpreted as
    // 1234*5 = 6170
    std::cout << " = " << doOperation(input) << '\n';

    return 0;
}
