#include "my_vector.h"

int main(void) {
    int arr[8] = { 67, 123, 2, 3, 4, -123, 52, 1 };
    struct Vector v = Vector_from_array(arr, sizeof(arr) / sizeof(int));

    Vector_sort(&v);
    Vector_write(&v, stdout);
    printf("\n");

    size_t start = 1;
    size_t end = 8;
    size_t length = (end - start);
    printf("Slice from start=%zu, end=%zu\n", start, end);

    int* slice = Vector_slice(&v, start, end);
    struct Vector v_slice = _Vector_from_array_heap(slice, length);
    Vector_write(&v_slice, stdout);
    printf("\n");

    int x = 41;
    size_t x_index = 0;
    printf("Inserting x=%d at x_index=%zu\n", x, x_index);
    Vector_insert(&v_slice, x, x_index);
    Vector_write(&v_slice, stdout);
    printf("\n");

    Vector_free(&v);
    Vector_free(&v_slice);

    return 0;
}
