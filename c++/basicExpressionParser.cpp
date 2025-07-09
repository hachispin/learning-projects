#include <cmath>
#include <iostream>
#include <stdexcept>
#include <string>
#include <tuple>

constexpr char ops[5] = { '+', '-', '*', '/', '^' };

std::string removeAllSpaces(std::string s) {
    for (int i = 0; i < s.size(); i++) {
        if (s[i] == ' ') {
            s.erase(i, 1);
            i--;
        }
    }
    return s;
}

bool isOperator(char chr) {
    for (char op : ops) {
        if (chr == op)
            return true;
    }
    return false;
}

int findOperatorIndex(std::string_view expr) {
    int opIdx = -1;
    for (int i = 0; i < expr.size(); i++) {
        if (isOperator(expr[i])) {
            opIdx = i; // this is fine because multiple operator exprs will be
            break;     // weeded out since right and left sides wont be valid numbers
        }
    }
    return opIdx;
}

std::tuple<std::string, std::string> // ordered (left, right) of index
splitByIndex(std::string_view sv, int idx) {
    if (idx > sv.size() - 1 || idx < 0)
        throw std::out_of_range("Provided index is outside string in splitByIndex");

    // doesn't include the character at the splitting index `idx`
    return { std::string(sv.substr(0, idx)), std::string(sv.substr(idx + 1)) };
}

// must have:
// - no leading zeroes
// - up to one dot which has numbers on both sides
// - only numbers and dots
bool isValidNumber(std::string_view s) {
    if (s[0] == '.' || s.back() == '.') // `.1` and `23.` isn't valid
        return false;
    if (s.size() > 1 && s[0] == '0' && s[1] != '.') // `00` isn't valid
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

// for the sake of simplicity, a valid expression here is defined
// as having one operator between two (valid) numeric substrings
bool isValidExpression(std::string_view expr) {
    int opIdx{ findOperatorIndex(expr) };

    if (expr.size() < 3)
        return false;
    if (opIdx == -1)
        return false;

    auto [left, right] = splitByIndex(expr, opIdx);

    if ( // clang-format off
        left.size() == 0        ||
        right.size() == 0       ||
        !isValidNumber(left)    ||
        !isValidNumber(right)
    ) // clang-format on
        return false;
    return true;
}

// takes inputs in the format:
//  a?b, where ? is a (valid) operator
// e.g. a + b
double doOperation(std::string_view expr) {
    // all of this is done assuming valid expr!
    int opIdx{ findOperatorIndex(expr) };
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
            throw std::runtime_error("Division by zero");
        return leftDouble / rightDouble;
    case '^':
        return std::pow(leftDouble, rightDouble);
    default:
        return 0.0; // should be unreachable
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
            int opIdx = findOperatorIndex(input);
            auto [left, right] = splitByIndex(input, opIdx);

            // division by zero
            if (input[opIdx] == '/' && std::stod(right) == 0.0) {
                std::cout << "You cannot divide by zero!\n";
                continue;
            }
        }
        break;
    }
    // TODO: trim spaces less aggresively because something like
    // 1 2 3 4 * 5
    // is interpreted as
    // 1234*5 = 6170
    std::cout << " = " << doOperation(input) << '\n';

    return 0;
}
