#include "aisl_format.h"

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static int failures;

static void write_u16_le(unsigned char *bytes, uint16_t value)
{
    bytes[0] = (unsigned char)value;
    bytes[1] = (unsigned char)(value >> 8);
}

static void write_u32_le(unsigned char *bytes, uint32_t value)
{
    bytes[0] = (unsigned char)value;
    bytes[1] = (unsigned char)(value >> 8);
    bytes[2] = (unsigned char)(value >> 16);
    bytes[3] = (unsigned char)(value >> 24);
}

static void write_u64_le(unsigned char *bytes, uint64_t value)
{
    write_u32_le(bytes, (uint32_t)value);
    write_u32_le(bytes + 4, (uint32_t)(value >> 32));
}

static int read_file(const char *path, unsigned char **bytes, size_t *size)
{
    FILE *file = fopen(path, "rb");
    long end;

    if (file == NULL || fseek(file, 0, SEEK_END) != 0 || (end = ftell(file)) < 0 ||
        fseek(file, 0, SEEK_SET) != 0) {
        if (file != NULL) fclose(file);
        return 0;
    }
    *size = (size_t)end;
    *bytes = malloc(*size == 0 ? 1 : *size);
    if (*bytes == NULL || fread(*bytes, 1, *size, file) != *size) {
        free(*bytes);
        fclose(file);
        return 0;
    }
    fclose(file);
    return 1;
}

static int write_file(const char *path, const unsigned char *bytes, size_t size)
{
    FILE *file = fopen(path, "wb");
    int wrote_all;
    int closed;

    if (file == NULL) return 0;
    wrote_all = fwrite(bytes, 1, size, file) == size;
    closed = fclose(file) == 0;
    return wrote_all && closed;
}

static void expect_status(const char *name, const char *path,
                          enum aisl_status expected)
{
    struct aisl_weights weights = {0, 0, NULL};
    enum aisl_status actual = aisl_weights_load(path, &weights);

    if (actual != expected) {
        fprintf(stderr, "FAIL %-22s expected '%s', got '%s'\n", name,
                aisl_status_string(expected), aisl_status_string(actual));
        ++failures;
    } else {
        printf("PASS %s\n", name);
    }
    aisl_weights_free(&weights);
}

static void mutate_and_test(const char *directory, const char *name,
                            unsigned char *bytes, size_t size,
                            enum aisl_status expected)
{
    char path[512];

    snprintf(path, sizeof(path), "%s/%s.bin", directory, name);
    if (!write_file(path, bytes, size)) {
        fprintf(stderr, "FAIL could not create %s\n", path);
        ++failures;
        return;
    }
    expect_status(name, path, expected);
}

int main(int argc, char **argv)
{
    struct aisl_weights weights = {0, 0, NULL};
    unsigned char *good;
    unsigned char *copy;
    size_t size;
    char path[512];

    if (argc != 3) {
        fprintf(stderr, "usage: %s GOOD_FILE TEMP_DIRECTORY\n", argv[0]);
        return 2;
    }
    if (!read_file(argv[1], &good, &size) || size != 56) {
        fprintf(stderr, "FAIL cannot read expected 56-byte fixture\n");
        return 1;
    }

    if (aisl_weights_load(argv[1], &weights) != AISL_OK ||
        weights.rows != 2 || weights.cols != 3 ||
        weights.data[0] != 1.0f || weights.data[5] != 6.0f) {
        fprintf(stderr, "FAIL valid file\n");
        ++failures;
    } else {
        printf("PASS valid file\n");
    }
    aisl_weights_free(&weights);

    snprintf(path, sizeof(path), "%s/empty.bin", argv[2]);
    mutate_and_test(argv[2], "empty", good, 0, AISL_ERR_TRUNCATED_HEADER);
    mutate_and_test(argv[2], "short-header", good, 31, AISL_ERR_TRUNCATED_HEADER);
    mutate_and_test(argv[2], "short-payload", good, 55, AISL_ERR_FILE_SIZE);

    copy = malloc(size + 1);
    if (copy == NULL) {
        free(good);
        return 1;
    }

#define RESET() memcpy(copy, good, size)
    RESET(); copy[0] = 'X';
    mutate_and_test(argv[2], "bad-magic", copy, size, AISL_ERR_MAGIC);
    RESET(); write_u16_le(copy + 4, 2);
    mutate_and_test(argv[2], "bad-version", copy, size, AISL_ERR_VERSION);
    RESET(); write_u16_le(copy + 6, 31);
    mutate_and_test(argv[2], "bad-header-size", copy, size, AISL_ERR_HEADER_SIZE);
    RESET(); write_u32_le(copy + 8, 99);
    mutate_and_test(argv[2], "bad-dtype", copy, size, AISL_ERR_DTYPE);
    RESET(); write_u32_le(copy + 12, 3);
    mutate_and_test(argv[2], "bad-rank", copy, size, AISL_ERR_RANK);
    RESET(); write_u32_le(copy + 16, 0);
    mutate_and_test(argv[2], "zero-shape", copy, size, AISL_ERR_SHAPE);
    RESET(); write_u32_le(copy + 16, UINT32_MAX); write_u32_le(copy + 20, UINT32_MAX);
    write_u64_le(copy + 24, UINT64_MAX);
    mutate_and_test(argv[2], "overflow", copy, size, AISL_ERR_OVERFLOW);
    RESET(); write_u64_le(copy + 24, 20);
    mutate_and_test(argv[2], "bad-data-size", copy, size, AISL_ERR_DATA_SIZE);
    RESET(); copy[size] = 0;
    mutate_and_test(argv[2], "extra-byte", copy, size + 1, AISL_ERR_FILE_SIZE);
#undef RESET

    free(copy);
    free(good);
    if (failures != 0) {
        fprintf(stderr, "%d test(s) failed\n", failures);
        return 1;
    }
    printf("reader tests: PASS\n");
    return 0;
}
