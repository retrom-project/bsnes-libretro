/*
  libco.emscripten (2020-02-27)
  authors: Toad King
  license: public domain
*/

#define LIBCO_C
#include "libco.h"
#include <stdlib.h>
#include <stddef.h>
#include <malloc.h>
#include <emscripten/fiber.h>

#define ASYNCIFY_STACK_SIZE (131072)

typedef struct {
   emscripten_fiber_t fiber;
   void *asyncify_stack;
   void *c_stack;
} co_fiber;

static co_fiber *co_active_;

static void co_thunk(void *coentry)
{
   ((void (*)(void))coentry)();
}

static void co_init(void)
{
   if (!co_active_)
   {
      co_fiber *co_primary = calloc(1, sizeof(co_fiber));
      co_primary->asyncify_stack = malloc(ASYNCIFY_STACK_SIZE);

      emscripten_fiber_init_from_current_context(&co_primary->fiber, co_primary->asyncify_stack, ASYNCIFY_STACK_SIZE);
      co_active_ = co_primary;
   }
}

cothread_t co_active(void)
{
   co_init();
   return co_active_;
}

cothread_t co_create(unsigned int stacksize, void (*coentry)(void))
{
   co_init();

   co_fiber *fiber = calloc(1, sizeof(co_fiber));
   fiber->asyncify_stack = malloc(ASYNCIFY_STACK_SIZE);
   fiber->c_stack = memalign(16, stacksize);
   emscripten_fiber_init(&fiber->fiber, co_thunk, coentry, fiber->c_stack, stacksize,
      fiber->asyncify_stack, ASYNCIFY_STACK_SIZE);

   return (cothread_t)fiber;
}

void co_delete(cothread_t cothread)
{
   co_fiber *fiber = (co_fiber *)cothread;
   free(fiber->c_stack);
   free(fiber->asyncify_stack);
   free(fiber);
}

void co_switch(cothread_t cothread)
{
   co_fiber *old_fiber = co_active_;
   co_active_ = (co_fiber *)cothread;

   emscripten_fiber_swap(&old_fiber->fiber, &co_active_->fiber);
}

/* Asyncify stacks contain runtime-owned state, not portable serialized bytes.
   bsnes must synchronize and recreate these fibers when restoring a state. */
int co_serializable(void)
{
   return 0;
}

cothread_t co_derive(void *memory, unsigned int stacksize, void (*coentry)(void))
{
   (void)memory;
   (void)stacksize;
   (void)coentry;
   return NULL;
}
