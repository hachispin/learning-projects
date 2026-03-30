#include <expected>
#include <format>
#include <iostream>
#include <ranges>
#include <string>
#include <tuple>
#include <vector>

namespace ranges = std::ranges;

#define MAP(fn) std::ranges::views::transform([](auto x) { return fn(x); })
#define EXPECT_NONZERO_DIMENSIONS                                                  \
    if (num_rows == 0) {                                                           \
        return std::unexpected(MatrixArrayError{                                   \
            MatrixArrayErrorType::InvalidDimensions, "num_rows cannot be zero" }); \
    }                                                                              \
                                                                                   \
    if (num_cols == 0) {                                                           \
        return std::unexpected(MatrixArrayError{                                   \
            MatrixArrayErrorType::InvalidDimensions, "num_cols cannot be zero" }); \
    }

enum class MatrixArrayErrorType {
    InvalidEntriesLength,
    InvalidDimensions,
};

struct MatrixArrayError {
    MatrixArrayErrorType type{};
    std::string message{};
};

/// Dimensions can't be changed after construction.
class MatrixArray {
  private:
    std::vector<double> entries{};
    size_t num_rows{};
    size_t num_cols{};

    /// This is private as it has no guards against invalid input by itself.
    MatrixArray(std::vector<double>&& entries, size_t num_rows, size_t num_cols)
        : entries(std::move(entries))
        , num_rows(num_rows)
        , num_cols(num_cols) {}

  public:
    using MatrixResult = std::expected<MatrixArray, MatrixArrayError>;

    // No sensible default here; a matrix with 0 entries, columns or
    // rows doesn't make sense (especially since dimensions can't change)
    MatrixArray() = delete;

    /// Consider using `std::move()` on `entries` if it's large.
    static MatrixResult create(std::vector<double> entries, size_t num_rows, size_t num_cols) {
        using MatrixArrayErrorType::InvalidEntriesLength;
        EXPECT_NONZERO_DIMENSIONS

        if (entries.size() != num_rows * num_cols) {
            const auto message = std::format(
                "expected entries to have length {}, instead got length {} (num_rows={}, num_cols={})",
                num_rows * num_cols, entries.size(), num_rows, num_cols);

            return std::unexpected(MatrixArrayError{
                InvalidEntriesLength,
                message,
            });
        }

        return MatrixArray{
            std::move(entries), num_rows, num_cols
        };
    }

    /// Returns the null/zero matrix for the given number of rows and columns.
    static MatrixResult null(size_t num_rows, size_t num_cols) {
        EXPECT_NONZERO_DIMENSIONS

        return MatrixArray{ std::vector(num_rows * num_cols, 0.0), num_rows, num_cols };
    }

    /// Returns the identity matrix I_n. Since identity matrices are
    /// square matrices, `n` is both the number of rows and columns.
    static MatrixResult identity(size_t n) {
        const auto m_res = MatrixArray::null(n, n);

        if (!m_res) {
            return m_res;
        }

        auto m = m_res.value();
        for (size_t i = 0; i < n; ++i) {
            m.entries[i * n + i] = 1.0;
        }

        return m;
    }

    auto get_num_rows() const { return num_rows; }
    auto get_num_cols() const { return num_cols; }
    auto get_dimensions() const { return std::tuple{ num_rows, num_cols }; }
    auto& get_entries() const { return entries; }
};

/// Converts a double to a string with some opinionated formatting choices.
std::string format_double(double d) {
    auto s = std::format("{:.{}f}", d, 2);
    s.erase(s.find_last_not_of('0') + 1);

    if (!s.empty() && s.back() == '.') {
        s.pop_back();
    }

    return s;
}

/// Wrapper over `MatrixEntries` implementing some methods.
class Matrix {
  private:
    MatrixArray inner;

  public:
    using MatrixResult = std::expected<Matrix, MatrixArrayError>;

    Matrix(MatrixArray m)
        : inner(m) {}

    static MatrixResult create(std::vector<double> entries, size_t num_rows, size_t num_cols) {
        return MatrixArray::create(entries, num_rows, num_cols)
            .and_then([](MatrixArray m) { return MatrixResult(Matrix{ m }); });
    }

    /// Displays the matrix in human-readable form.
    /// Note that this leaves a trailing newline.
    ///
    /// Formatting should look like this:
    /// ┌ 1 2 3 ┐               ┌ 12 345  6  ┐
    /// │ 4 5 6 │ or [1 2 3] or │ 7   8   9  │
    /// └ 7 8 9 ┘               └ 10 11  123 ┘
    ///
    /// Formatting should have
    std::ostream& display(std::ostream& out) const {
        // Simple case: just a square bracket
        if (inner.get_num_cols() == 1) {
            out << '[';

            for (const auto i : inner.get_entries()) {
                out << format_double(i);
            }

            return out << "]\n";
        }

        auto entries_str =
            inner.get_entries()
            | ranges::views::transform(format_double)
            | ranges::to<std::vector>();

        // for column j, length should be padded to col_spacings[j]

        exit(0);
    }

    auto get_num_rows() const { return inner.get_num_rows(); }
    auto get_num_cols() const { return inner.get_num_cols(); }
    auto& get_entries() const { return inner.get_entries(); }

    /// Returns (num_rows, num_cols).
    std::tuple<size_t, size_t> get_dimensions() const {
        return { inner.get_num_rows(), inner.get_num_cols() };
    }
};

int main() {
    auto m_res = Matrix::create(std::vector<double>{}, 1, 2);
    auto m = m_res.value();
}
