# this is contents for the -tools repository

ENVAR := TMPDIR=$(shell pwd)/build
PIP_OPTS := --disable-pip-version-check --timeout 30 --retries 60 --quiet
NOSE_OPTS := --verbose
NAME := dagger

ifeq ($(shell uname),Darwin)
   PIP_OPTS += --no-cache-dir
endif


ifeq ($(OS),Windows_NT)
   VENV := . .virtualenv/$(NAME)/Scripts/activate
else
   VENV := . .virtualenv/$(NAME)/bin/activate

   # only enable paralallel test runs on Linux and OS X systems;
   # windows systems reliably hit the timeouts.
   PARALLEL_NOSE_OPTS = --processes 12 --process-timeout 200
   ifneq ($(RUN_PARALLEL_NOSE),)
      # require that an envar be set to run nose in a parallel mode
      # typically a developer would only want to run this locally.
      NOSE_OPTS += $(PARALLEL_NOSE_OPTS)
   endif

endif

NOSE_OPTS += --with-randomly

.PHONY:virtualenv install test-deps deps
activate:
	@echo $(VENV)
noseopts:
	@echo $(NOSE_OPTS)
env:
	@echo $(ENVAR)
virtualenv:.virtualenv/$(NAME)
	@echo "[env] virtualenv at $<, activate with: $(VENV)"
.virtualenv:
	mkdir $@
.virtualenv/$(NAME):.virtualenv
# use python2 on arch linux.
ifneq (,$(wildcard /etc/arch-release))
	virtualenv2 -p /usr/bin/python2 $@
else
	virtualenv --system-site-packages $@
endif

clean:
	-rm -fr .virtualenv/
	-find $(NAME) -name "*.pyc" | xargs rm -f
	-find test -name "*.pyc" | xargs rm -f

deps:.virtualenv/$(NAME)
	$(VENV); pip $(PIP_OPTS) install -r requirements.txt
	@echo "[deps]: installed all required python packages"

test-deps:.virtualenv/$(NAME) install
	$(VENV); pip $(PIP_OPTS) install nose nose-randomly
	@echo "[deps]: installed all development packages"

lint-deps:.virtualenv/$(NAME)
	$(VENV); pip $(PIP_OPTS) install pyflakes pep8

coverage-deps:test-deps
	$(VENV); pip $(PIP_OPTS) install coverage

lint:lint-deps
	$(VENV); pep8 --max-line-length=100 $(NAME) test
	$(VENV); pyflakes $(NAME) test

install:deps
	$(VENV); pip $(PIP_OPTS) install -e .
	$(VENV); $(NAME) version

test:test-deps
	$(VENV); $(ENVAR) nosetests $(NOSE_OPTS)

coverage:coverage-deps
	$(VENV); $(ENVAR) nosetests $(PARALLEL_NOSE_OPTS) --verbose --with-coverage  --cover-erase --cover-min-percentage=80 --cover-inclusive --cover-package $(NAME)
