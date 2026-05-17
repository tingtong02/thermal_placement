#include <stdint.h>

#include "include/gemmini.h"

extern void printstr(const char *s);

static elem_t A[DIM][DIM] row_align(1);
static elem_t B[DIM][DIM] row_align(1);
static elem_t C[DIM][DIM] row_align(1);
static elem_t gold[DIM][DIM];

static void init_inputs(void) {
  for (int i = 0; i < DIM; ++i) {
    for (int j = 0; j < DIM; ++j) {
      A[i][j] = ((i + j) & 1) ? 1 : 0;
      B[i][j] = ((i * 3 + j) & 1) ? 1 : 0;
      C[i][j] = 0;
    }
  }
}

static void compute_gold(void) {
  for (int i = 0; i < DIM; ++i) {
    for (int j = 0; j < DIM; ++j) {
      int32_t sum = 0;
      for (int k = 0; k < DIM; ++k) {
        sum += (int32_t)A[i][k] * (int32_t)B[k][j];
      }
      gold[i][j] = (elem_t)sum;
    }
  }
}

static int check_result(void) {
  for (int i = 0; i < DIM; ++i) {
    for (int j = 0; j < DIM; ++j) {
      if (C[i][j] != gold[i][j]) {
        return 1;
      }
    }
  }
  return 0;
}

int main(void) {
  const uint32_t a_sp_addr = 0;
  const uint32_t b_sp_addr = DIM;
  const uint32_t c_sp_addr = 2 * DIM;

  printstr("small-gemm-start\n");

  init_inputs();
  compute_gold();

  gemmini_flush(0);
  gemmini_config_ld(DIM * sizeof(elem_t));
  gemmini_config_st(DIM * sizeof(elem_t));

  gemmini_mvin(A, a_sp_addr);
  gemmini_mvin(B, b_sp_addr);

  gemmini_extended_config_ex(OUTPUT_STATIONARY, NO_ACTIVATION, 0, 1, false, false);
  gemmini_preload_zeros(c_sp_addr);
  gemmini_compute_preloaded(a_sp_addr, b_sp_addr);
  gemmini_mvout(C, c_sp_addr);
  gemmini_fence();

  if (check_result()) {
    printstr("small-gemm-fail\n");
    return 1;
  }

  printstr("small-gemm-ok\n");
  return 0;
}
