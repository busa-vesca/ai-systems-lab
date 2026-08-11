#include "aisl_format.h"

#include <float.h>
#include <limits.h>
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

_Static_assert(CHAR_BIT == 8, "AISL requires 8-bit bytes");
_Static_assert(sizeof(float) == 4, "AISL requires 32-bit float");
_Static_assert(FLT_RADIX == 2 && FLT_MANT_DIG == 24 && FLT_MAX_EXP == 128,
               "AISL requires IEEE-754 binary32 float");

static uint16_t read_u16_le(const unsigned char *bytes)
{
    return (uint16_t)bytes[0] | ((uint16_t)bytes[1] << 8);
}

static uint32_t read_u32_le(const unsigned char *bytes)
{
    return (uint32_t)bytes[0] |
           ((uint32_t)bytes[1] << 8) |
           ((uint32_t)bytes[2] << 16) |
           ((uint32_t)bytes[3] << 24);
}

static uint64_t read_u64_le(const unsigned char *bytes)
{
    return (uint64_t)read_u32_le(bytes) |
           ((uint64_t)read_u32_le(bytes + 4) << 32);
}

static float read_f32_le(const unsigned char *bytes)
{
    uint32_t bits = read_u32_le(bytes);
    float value;

    memcpy(&value, &bits, sizeof(value));
    return value;
}

static enum aisl_status get_file_size(FILE *file, uint64_t *size)
{
    long end;

    if (fseek(file, 0L, SEEK_END) != 0) {
        return AISL_ERR_SEEK;
    }
    end = ftell(file);
    if (end < 0) {
        return AISL_ERR_SEEK;
    }
    if (fseek(file, 0L, SEEK_SET) != 0) {
        return AISL_ERR_SEEK;
    }
    *size = (uint64_t)end;
    return AISL_OK;
}

void aisl_weights_free(struct aisl_weights *weights)
{
    if (weights == NULL) {
        return;
    }
    free(weights->data);
    weights->data = NULL;
    weights->rows = 0;
    weights->cols = 0;
}

enum aisl_status aisl_weights_load(const char *path, struct aisl_weights *out)
{
    static const unsigned char magic[AISL_MAGIC_SIZE] = {'A', 'I', 'S', 'L'};
    unsigned char header[AISL_HEADER_SIZE];
    unsigned char element_bytes[sizeof(float)];
    uint16_t version;
    uint16_t header_size;
    uint32_t dtype;
    uint32_t rank;
    uint32_t rows;
    uint32_t cols;
    uint64_t declared_data_size;
    uint64_t element_count;
    uint64_t expected_data_size;
    uint64_t expected_file_size;
    uint64_t file_size;
    size_t i;
    FILE *file;
    enum aisl_status status;

    if (path == NULL || out == NULL) {
        return AISL_ERR_ARGUMENT;
    }
    out->rows = 0;
    out->cols = 0;
    out->data = NULL;

    file = fopen(path, "rb");
    if (file == NULL) {
        return AISL_ERR_OPEN;
    }

    status = get_file_size(file, &file_size);
    if (status != AISL_OK) {
        fclose(file);
        return status;
    }
    if (file_size < AISL_HEADER_SIZE) {
        fclose(file);
        return AISL_ERR_TRUNCATED_HEADER;
    }
    if (fread(header, 1, sizeof(header), file) != sizeof(header)) {
        fclose(file);
        return AISL_ERR_READ;
    }

    if (memcmp(header, magic, sizeof(magic)) != 0) {
        fclose(file);
        return AISL_ERR_MAGIC;
    }
    version = read_u16_le(header + 4);
    header_size = read_u16_le(header + 6);
    dtype = read_u32_le(header + 8);
    rank = read_u32_le(header + 12);
    rows = read_u32_le(header + 16);
    cols = read_u32_le(header + 20);
    declared_data_size = read_u64_le(header + 24);

    if (version != AISL_VERSION) {
        status = AISL_ERR_VERSION;
    } else if (header_size != AISL_HEADER_SIZE) {
        status = AISL_ERR_HEADER_SIZE;
    } else if (dtype != AISL_DTYPE_F32) {
        status = AISL_ERR_DTYPE;
    } else if (rank != AISL_RANK_MATRIX) {
        status = AISL_ERR_RANK;
    } else if (rows == 0 || cols == 0) {
        status = AISL_ERR_SHAPE;
    } else if ((uint64_t)rows > UINT64_MAX / (uint64_t)cols) {
        status = AISL_ERR_OVERFLOW;
    } else {
        element_count = (uint64_t)rows * (uint64_t)cols;
        if (element_count > UINT64_MAX / sizeof(float) ||
            element_count > SIZE_MAX / sizeof(float)) {
            status = AISL_ERR_OVERFLOW;
        } else {
            expected_data_size = element_count * sizeof(float);
            if (declared_data_size != expected_data_size) {
                status = AISL_ERR_DATA_SIZE;
            } else if (declared_data_size > UINT64_MAX - AISL_HEADER_SIZE) {
                status = AISL_ERR_OVERFLOW;
            } else {
                expected_file_size = AISL_HEADER_SIZE + declared_data_size;
                status = file_size == expected_file_size
                             ? AISL_OK
                             : AISL_ERR_FILE_SIZE;
            }
        }
    }

    if (status != AISL_OK) {
        fclose(file);
        return status;
    }

    out->data = malloc((size_t)expected_data_size);
    if (out->data == NULL) {
        fclose(file);
        return AISL_ERR_ALLOC;
    }
    out->rows = rows;
    out->cols = cols;

    for (i = 0; i < (size_t)element_count; ++i) {
        if (fread(element_bytes, 1, sizeof(element_bytes), file) !=
            sizeof(element_bytes)) {
            aisl_weights_free(out);
            fclose(file);
            return AISL_ERR_READ;
        }
        out->data[i] = read_f32_le(element_bytes);
    }

    if (fclose(file) != 0) {
        aisl_weights_free(out);
        return AISL_ERR_READ;
    }
    return AISL_OK;
}

const char *aisl_status_string(enum aisl_status status)
{
    switch (status) {
    case AISL_OK: return "ok";
    case AISL_ERR_ARGUMENT: return "invalid argument";
    case AISL_ERR_OPEN: return "cannot open file";
    case AISL_ERR_SEEK: return "cannot determine file size";
    case AISL_ERR_READ: return "file read failed";
    case AISL_ERR_TRUNCATED_HEADER: return "truncated header";
    case AISL_ERR_MAGIC: return "invalid magic";
    case AISL_ERR_VERSION: return "unsupported version";
    case AISL_ERR_HEADER_SIZE: return "invalid header size";
    case AISL_ERR_DTYPE: return "unsupported data type";
    case AISL_ERR_RANK: return "unsupported tensor rank";
    case AISL_ERR_SHAPE: return "invalid tensor shape";
    case AISL_ERR_OVERFLOW: return "size arithmetic overflow";
    case AISL_ERR_DATA_SIZE: return "data size does not match shape";
    case AISL_ERR_FILE_SIZE: return "file size does not match header";
    case AISL_ERR_ALLOC: return "memory allocation failed";
    }
    return "unknown error";
}
