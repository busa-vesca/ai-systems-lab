#include "aisl_format.h"

#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>

int main(int argc, char **argv)
{
    struct aisl_weights weights = {0, 0, NULL};
    enum aisl_status status;
    uint64_t count;
    uint64_t i;

    if (argc != 2) {
        fprintf(stderr, "usage: %s FILE\n", argv[0]);
        return 2;
    }

    status = aisl_weights_load(argv[1], &weights);
    if (status != AISL_OK) {
        fprintf(stderr, "load failed: %s\n", aisl_status_string(status));
        return 1;
    }

    count = (uint64_t)weights.rows * weights.cols;
    printf("format: AISL\n");
    printf("version: %u\n", AISL_VERSION);
    printf("dtype: fp32\n");
    printf("shape: %" PRIu32 " x %" PRIu32 "\n", weights.rows, weights.cols);
    printf("elements: %" PRIu64 "\n", count);
    printf("data bytes: %" PRIu64 "\n", count * sizeof(float));
    printf("values:");
    for (i = 0; i < count; ++i) {
        printf(" %g", (double)weights.data[i]);
    }
    putchar('\n');

    aisl_weights_free(&weights);
    return 0;
}
