dev:
	@./webapp/shoreman.sh

tail-log:
	@cat ./webapp/dev.log

build-whisper:
	@echo "Building whisper.cpp..."
	cd whisper.cpp && make -j$(shell nproc 2>/dev/null || sysctl -n hw.ncpu 2>/dev/null || echo 4)
	@echo "Downloading ggml-large-v3-turbo model..."
	cd whisper.cpp && ./models/download-ggml-model.sh large-v3-turbo
