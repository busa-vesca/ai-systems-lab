#ifndef AISL_FORMAT_H
#define AISL_FORMAT_H

#include <stdint.h>

#define AISL_MAGIC_SIZE 4u
#define AISL_HEADER_SIZE 32u
#define AISL_VERSION 1u
#define AISL_DTYPE_F32 1u
#define AISL_RANK_MATRIX 2u

struct aisl_weights {
    uint32_t rows;
    uint32_t cols;
    float *data;
};

enum aisl_status {
    AISL_OK = 0,
    AISL_ERR_ARGUMENT,
    AISL_ERR_OPEN,
    AISL_ERR_SEEK,
    AISL_ERR_READ,
    AISL_ERR_TRUNCATED_HEADER,
    AISL_ERR_MAGIC,
    AISL_ERR_VERSION,
    AISL_ERR_HEADER_SIZE,
    AISL_ERR_DTYPE,
    AISL_ERR_RANK,
    AISL_ERR_SHAPE,
    AISL_ERR_OVERFLOW,
    AISL_ERR_DATA_SIZE,
    AISL_ERR_FILE_SIZE,
    AISL_ERR_ALLOC
};

enum aisl_status aisl_weights_load(const char *path, struct aisl_weights *out);
void aisl_weights_free(struct aisl_weights *weights);
const char *aisl_status_string(enum aisl_status status);

#endif
