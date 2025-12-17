#include "my_vector.h"
#include <errno.h>
#include <limits.h>
#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

// creates a new vector with 0 elements and 0 capacity
struct Vector Vector_new(void) {
    return (struct Vector) { .ptr = nullptr };
}

// creates a vector by copying elements of `arr`
struct Vector Vector_from_array(const int* arr, size_t length) {
    if (length == 0) {
        return Vector_new();
    }

    size_t capacity = 1;

    while (capacity < length) {
        capacity *= 2;
    }

    size_t ptr_size = capacity * sizeof(int);
    int* ptr = malloc(capacity * sizeof(int));

    if (ptr == nullptr) {
        fprintf(stderr, "%s(): malloc failed, ptr_size=%zu\n",
                __func__, ptr_size);

        exit(1);
    }

    memcpy(ptr, arr, length * sizeof(int));

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
static void _Vector_expand(struct Vector* v) {
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
static void _Vector_check_expand(struct Vector* v) {
    if (v->capacity == 0 || v->length >= v->capacity) {
        _Vector_expand(v);
    }
}

// shifts all elements right of `pivot` by `offset`
//
// this does not include `pivot` itself
static void _Vector_rshift(struct Vector* v, size_t pivot, size_t offset) {
#ifdef DEBUG
    if (pivot >= v->length) {
        fprintf(
            stderr,
            "%s(): `pivot` out of bounds; length=%zu, pivot=%zu, offset=%zu\n",
            __func__, v->length, pivot, offset);

        exit(1);
    }
#endif
    if (offset == 0) {
        return;
    }

    size_t start = pivot + 1;
    size_t tail_len = v->length - start;
    v->length += offset;
    _Vector_check_expand(v);

    memmove(&v->ptr[start + offset], &v->ptr[start], tail_len * sizeof(int));
}

// returns an array containing all elements at indices `start <= i < end`
//
// note: the returned slice must be freed
int* Vector_slice_arr(const struct Vector* v, size_t start, size_t end) {
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

// returns a vector containing all elements at indices `start <= i < end`
struct Vector Vector_slice_vec(const struct Vector* v, size_t start, size_t end) {
    int* slice = Vector_slice_arr(v, start, end);
    return _Vector_from_array_heap(slice, end - start);
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
    // no need to increment `v->length`, done in `_Vector_rshift()`
    _Vector_rshift(v, index, 1);
    v->ptr[index] = element;
}

// pushes the given element to the end of `v->ptr`
void Vector_push(struct Vector* v, int element) {
    _Vector_check_expand(v);

    v->ptr[v->length++] = element;
}

// extends the given vector, `v`, by the array, `ext`
void Vector_extend_arr(struct Vector* v, const int* ext, size_t length) {
    if (length == 0) {
        return;
    }

    size_t start = v->length;

    // this changes `v->length`
    _Vector_rshift(v, v->length - 1, length);

    for (size_t i = start; i < v->length; ++i) {
#ifdef DEBUG
        if (i < start) {
            fprintf(stderr, "%s(): overflow\n", __func__);
            exit(1);
        }
#endif
        memcpy(&v->ptr[i], &ext[i - start], sizeof(int));
    }
}

// extends the given vector, `v`, by the vector, `ext`
void Vector_extend_vec(struct Vector* v, const struct Vector* ext) {
    size_t start = v->length;
    v->length += ext->length;
    _Vector_check_expand(v);

    for (size_t i = start; i < v->length; ++i) {
        v->ptr[i] = ext->ptr[i];
    }
}

// writes the contents of the vector to the stream, `f`
//
// if `newline` is true, "\n" is added to the end
void Vector_write(const struct Vector* v, FILE* f, bool newline) {
    for (size_t i = 0; i < v->length; ++i) {
        fprintf(f, "%d ", v->ptr[i]);
    }

    if (newline) {
        fprintf(f, "\n");
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
