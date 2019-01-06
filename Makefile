all: build

build:
	(cd md2ht; cargo install --force --path .)
	(cd blog; ./scripts/compile.py)
	rm -rf main
	cp -r ./blog/bin ./main
	rm -rf blog/bin

deploy: build
	gcloud app deploy app.yaml --project imcluelesssoftware
