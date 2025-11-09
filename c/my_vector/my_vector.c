#include "my_vector.h"
#include <errno.h>
#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>

// creates a new vector with 0 elements and 0 capacity
struct Vector Vector_new(void) {
    int* ptr = NULL;
    size_t length = 0;
    size_t capacity = 0;

    return (struct Vector) {
        .ptr = ptr, .length = length, .capacity = capacity
    };
}

// creates a vector by copying elements of `arr`
struct Vector Vector_from_array(const int* arr, size_t length) {
    size_t capacity = 1;

    while (capacity < length) {
        capacity *= 2;
    }

    int* ptr = malloc(capacity * sizeof(int));

    for (size_t i = 0; i < length; ++i) {
        ptr[i] = arr[i];
    }

    return (struct Vector) {
        .ptr = ptr, .length = length, .capacity = capacity
    };
}

// creates a vector from (moved) elements of `arr`, invalidating it
//
// note: do not free `arr` if the returned `Vector` is still in use
struct Vector _Vector_from_array_heap(int* arr, size_t length) {
    size_t capacity = 1;

    while (capacity < length) {
        capacity *= 2;
    }

    struct Vector v = {
        .ptr = arr, .length = length, .capacity = capacity
    };

    return v;
}

// increases `v->capacity` exponentially and reallocs `v->ptr`
void _Vector_expand(struct Vector* v) {
    if (v->capacity == 0) {
        v->capacity = 1;
    } else {
        v->capacity *= 2;
    }

    int* tmp = realloc(v->ptr, v->capacity * sizeof(int));

    if (tmp == nullptr) {
        fprintf(stderr, "%s(): vector realloc failed\n", __func__);
        fprintf(stderr, "size=%zu, errno=%d\n", v->capacity, errno);
        Vector_free(v);
        exit(1);
    }

    v->ptr = tmp;
}

// calls `_Vector_expand(v)` if needed, else, does nothing
void _Vector_check_expand(struct Vector* v) {
    if (v->capacity == 0 || v->length >= v->capacity) {
        _Vector_expand(v);
    }
}

// returns an array containing all elements at indices `start <= i < end`
//
// note: the returned slice must be freed
int* Vector_slice(const struct Vector* v, size_t start, size_t end) {
#ifdef DEBUG
    if (start > end || end > v->length) {
        fprintf(
            stderr,
            "%s(): invalid slice; start=%zu, end=%zu, v->length=%zu\n",
            __func__, start, end, v->length);

        exit(1);
    }
#endif

    // heap alloc because slice can be arbitrary large
    size_t size = end - start;
    int* slice = malloc(size * sizeof(int));

    if (slice == nullptr) {
        fprintf(stderr, "%s(): slice malloc failed\n", __func__);
        fprintf(stderr, "size=%zu, errno=%d\n", size, errno);
        exit(1);
    }

    for (size_t i = start; i < end; ++i) {
        slice[i - start] = v->ptr[i];
    }

    return slice;
}

// inserts the given `element` at `index`
void Vector_insert(struct Vector* v, int element, size_t index) {
#ifdef DEBUG
    if (index >= v->length) {
        fprintf(
            stderr,
            "%s(): insert out of bounds; index=%zu, length=%zu\n",
            __func__, index, v->length);

        exit(1);
    }
#endif

    ++v->length;
    _Vector_check_expand(v);

    // shift right of `index` by 1 for `element`
    for (size_t i = v->length - 1; i > index; --i) {
        v->ptr[i] = v->ptr[i - 1];
    }

    v->ptr[index] = element;
}

// pushes the given element to the end of `v->ptr`
void Vector_push(struct Vector* v, int element) {
    _Vector_check_expand(v);

    v->ptr[v->length++] = element;
}

// writes the contents of the vector to the stream, `f`
void Vector_write(const struct Vector* v, FILE* f) {
    for (size_t i = 0; i < v->length; ++i) {
        fprintf(f, "%d ", v->ptr[i]);
    }
}

// sorts the array using bubble sort in ascending order
void Vector_sort(struct Vector* v) {
    if (v->length <= 1) {
        return;
    }

    bool swapping = true;
    size_t effective_length = v->length;

    while (swapping) {
        swapping = false;
        --effective_length;

        for (size_t i = 0; i < effective_length; ++i) {
            if (v->ptr[i] > v->ptr[i + 1]) {
                swapping = true;
                int tmp = v->ptr[i];
                v->ptr[i] = v->ptr[i + 1];
                v->ptr[i + 1] = tmp;
            }
        }
    }
}

// frees heap members and sets other members to 0
void Vector_free(struct Vector* v) {
    free(v->ptr);
    v->ptr = nullptr;
    v->length = 0;
    v->capacity = 0;
}
