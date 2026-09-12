#include <assert.h>
#include "libco/libco.h"

static cothread_t primary;
static int steps;
static void worker(void) {
  ++steps;
  co_switch(primary);
  ++steps;
  co_switch(primary);
  assert(0);
}
int main(void) {
  primary = co_active();
  assert(!co_serializable());
  assert(co_derive(0, 0, worker) == 0);
  for (int i = 0; i < 100; ++i) {
    cothread_t task = co_create(16384, worker);
    assert(task && task != primary);
    co_switch(task);
    assert(steps == i * 2 + 1 && co_active() == primary);
    co_switch(task);
    assert(steps == i * 2 + 2 && co_active() == primary);
    co_delete(task);
  }
  return 0;
}
