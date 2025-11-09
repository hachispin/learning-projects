#ifndef MY_VECTOR_H
#define MY_VECTOR_H

#include <stddef.h>
#include <stdio.h>

// `capacity` is not in bytes; it's more like the max length
struct Vector {
    int* ptr;
    size_t length;
    size_t capacity;
};

struct Vector Vector_new(void);
struct Vector Vector_from_array(const int* arr, size_t length);
struct Vector _Vector_from_array_heap(int* arr, size_t length);
void _Vector_expand(struct Vector* v);
int* Vector_slice(const struct Vector* v, size_t start, size_t end);
void Vector_insert(struct Vector* v, int element, size_t index);
void Vector_push(struct Vector* v, int element);
void Vector_write(const struct Vector* v, FILE* f);
void Vector_sort(struct Vector* v);
void Vector_free(struct Vector* v);

#endif
