CC ?= cc
CFLAGS := -std=c11 -Wall -Wextra -Wpedantic -Iinclude
BUILD := build

.PHONY: all test sanitize clean

all: $(BUILD)/inspect_weights

$(BUILD):
	mkdir -p $(BUILD)

$(BUILD)/inspect_weights: src/inspect_weights.c src/weight_reader.c include/aisl_format.h | $(BUILD)
	$(CC) $(CFLAGS) src/inspect_weights.c src/weight_reader.c -o $@

$(BUILD)/test_reader: tests/test_reader.c src/weight_reader.c include/aisl_format.h | $(BUILD)
	$(CC) $(CFLAGS) tests/test_reader.c src/weight_reader.c -o $@

$(BUILD)/test_reader_sanitize: tests/test_reader.c src/weight_reader.c include/aisl_format.h | $(BUILD)
	$(CC) $(CFLAGS) -g -O1 -fsanitize=address,undefined -fno-omit-frame-pointer \
		tests/test_reader.c src/weight_reader.c -o $@

$(BUILD)/weights.bin: tools/export_weights.py | $(BUILD)
	python3 tools/export_weights.py $@

test: $(BUILD)/inspect_weights $(BUILD)/test_reader $(BUILD)/weights.bin
	python3 tests/test_exporter.py
	$(BUILD)/test_reader $(BUILD)/weights.bin $(BUILD)
	$(BUILD)/inspect_weights $(BUILD)/weights.bin

sanitize: $(BUILD)/test_reader_sanitize $(BUILD)/weights.bin
	$(BUILD)/test_reader_sanitize $(BUILD)/weights.bin $(BUILD)

clean:
	rm -rf $(BUILD)
