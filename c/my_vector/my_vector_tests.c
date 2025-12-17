#include "my_vector.h"
#include <assert.h>
#include <limits.h>
#include <stdlib.h>

// used for testing capacity calculations, rounds `x` to next pow 2
size_t next_pow2(size_t x) {
    size_t pow2 = 1;

    while (pow2 < x) {
        pow2 *= 2;
    }

    return x;
}

int test_Vector_from_array(void) {
    int arr[6] = { 1, 2, 3, 4, 5, 6 };
    size_t arr_len = sizeof(arr) / sizeof(int);
    struct Vector arr_v = Vector_from_array(arr, arr_len);

    int* v_expected_ptr = malloc(arr_len * sizeof(int));
    struct Vector v_expected = {
        v_expected_ptr, arr_len, next_pow2(arr_len)
    };
}
