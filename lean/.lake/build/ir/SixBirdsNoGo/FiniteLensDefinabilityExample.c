// Lean compiler output
// Module: SixBirdsNoGo.FiniteLensDefinabilityExample
// Imports: public import Init public import SixBirdsNoGo.FiniteLensDefinability
#include <lean/lean.h>
#if defined(__clang__)
#pragma clang diagnostic ignored "-Wunused-parameter"
#pragma clang diagnostic ignored "-Wunused-label"
#elif defined(__GNUC__) && !defined(__CLANG__)
#pragma GCC diagnostic ignored "-Wunused-parameter"
#pragma GCC diagnostic ignored "-Wunused-label"
#pragma GCC diagnostic ignored "-Wunused-but-set-variable"
#endif
#ifdef __cplusplus
extern "C" {
#endif
LEAN_EXPORT lean_object* lp_sixbirdsnogo_SixBirdsNoGo_lens3to2___lam__0___boxed(lean_object*);
LEAN_EXPORT uint8_t lp_sixbirdsnogo_SixBirdsNoGo_assignFalse(lean_object*);
static lean_object* lp_sixbirdsnogo_SixBirdsNoGo_lens3to2___closed__0;
static lean_object* lp_sixbirdsnogo_SixBirdsNoGo_lens3to2___closed__1;
uint8_t lean_nat_dec_eq(lean_object*, lean_object*);
LEAN_EXPORT lean_object* lp_sixbirdsnogo_SixBirdsNoGo_assignFalse___boxed(lean_object*);
lean_object* lean_nat_sub(lean_object*, lean_object*);
LEAN_EXPORT lean_object* lp_sixbirdsnogo_SixBirdsNoGo_assignHeadTrue___boxed(lean_object*);
LEAN_EXPORT lean_object* lp_sixbirdsnogo_SixBirdsNoGo_lens3to2___lam__0(lean_object*);
LEAN_EXPORT uint8_t lp_sixbirdsnogo_SixBirdsNoGo_assignHeadTrue(lean_object*);
LEAN_EXPORT lean_object* lp_sixbirdsnogo_SixBirdsNoGo_lens3to2;
LEAN_EXPORT lean_object* lp_sixbirdsnogo_SixBirdsNoGo_lens3to2___lam__0(lean_object* x_1) {
_start:
{
lean_object* x_2; uint8_t x_3; 
x_2 = lean_unsigned_to_nat(0u);
x_3 = lean_nat_dec_eq(x_1, x_2);
if (x_3 == 0)
{
lean_object* x_4; 
x_4 = lean_unsigned_to_nat(1u);
return x_4;
}
else
{
return x_2;
}
}
}
LEAN_EXPORT lean_object* lp_sixbirdsnogo_SixBirdsNoGo_lens3to2___lam__0___boxed(lean_object* x_1) {
_start:
{
lean_object* x_2; 
x_2 = lp_sixbirdsnogo_SixBirdsNoGo_lens3to2___lam__0(x_1);
lean_dec(x_1);
return x_2;
}
}
static lean_object* _init_lp_sixbirdsnogo_SixBirdsNoGo_lens3to2___closed__0() {
_start:
{
lean_object* x_1; 
x_1 = lean_alloc_closure((void*)(lp_sixbirdsnogo_SixBirdsNoGo_lens3to2___lam__0___boxed), 1, 0);
return x_1;
}
}
static lean_object* _init_lp_sixbirdsnogo_SixBirdsNoGo_lens3to2___closed__1() {
_start:
{
lean_object* x_1; lean_object* x_2; lean_object* x_3; lean_object* x_4; 
x_1 = lp_sixbirdsnogo_SixBirdsNoGo_lens3to2___closed__0;
x_2 = lean_unsigned_to_nat(2u);
x_3 = lean_unsigned_to_nat(3u);
x_4 = lean_alloc_ctor(0, 3, 0);
lean_ctor_set(x_4, 0, x_3);
lean_ctor_set(x_4, 1, x_2);
lean_ctor_set(x_4, 2, x_1);
return x_4;
}
}
static lean_object* _init_lp_sixbirdsnogo_SixBirdsNoGo_lens3to2() {
_start:
{
lean_object* x_1; 
x_1 = lp_sixbirdsnogo_SixBirdsNoGo_lens3to2___closed__1;
return x_1;
}
}
LEAN_EXPORT uint8_t lp_sixbirdsnogo_SixBirdsNoGo_assignFalse(lean_object* x_1) {
_start:
{
uint8_t x_2; 
x_2 = 0;
return x_2;
}
}
LEAN_EXPORT lean_object* lp_sixbirdsnogo_SixBirdsNoGo_assignFalse___boxed(lean_object* x_1) {
_start:
{
uint8_t x_2; lean_object* x_3; 
x_2 = lp_sixbirdsnogo_SixBirdsNoGo_assignFalse(x_1);
lean_dec(x_1);
x_3 = lean_box(x_2);
return x_3;
}
}
LEAN_EXPORT uint8_t lp_sixbirdsnogo_SixBirdsNoGo_assignHeadTrue(lean_object* x_1) {
_start:
{
lean_object* x_2; uint8_t x_3; 
x_2 = lean_unsigned_to_nat(0u);
x_3 = lean_nat_dec_eq(x_1, x_2);
if (x_3 == 1)
{
return x_3;
}
else
{
lean_object* x_4; lean_object* x_5; uint8_t x_6; 
x_4 = lean_unsigned_to_nat(1u);
x_5 = lean_nat_sub(x_1, x_4);
x_6 = lean_nat_dec_eq(x_5, x_2);
lean_dec(x_5);
return x_3;
}
}
}
LEAN_EXPORT lean_object* lp_sixbirdsnogo_SixBirdsNoGo_assignHeadTrue___boxed(lean_object* x_1) {
_start:
{
uint8_t x_2; lean_object* x_3; 
x_2 = lp_sixbirdsnogo_SixBirdsNoGo_assignHeadTrue(x_1);
lean_dec(x_1);
x_3 = lean_box(x_2);
return x_3;
}
}
lean_object* initialize_Init(uint8_t builtin);
lean_object* initialize_sixbirdsnogo_SixBirdsNoGo_FiniteLensDefinability(uint8_t builtin);
static bool _G_initialized = false;
LEAN_EXPORT lean_object* initialize_sixbirdsnogo_SixBirdsNoGo_FiniteLensDefinabilityExample(uint8_t builtin) {
lean_object * res;
if (_G_initialized) return lean_io_result_mk_ok(lean_box(0));
_G_initialized = true;
res = initialize_Init(builtin);
if (lean_io_result_is_error(res)) return res;
lean_dec_ref(res);
res = initialize_sixbirdsnogo_SixBirdsNoGo_FiniteLensDefinability(builtin);
if (lean_io_result_is_error(res)) return res;
lean_dec_ref(res);
lp_sixbirdsnogo_SixBirdsNoGo_lens3to2___closed__0 = _init_lp_sixbirdsnogo_SixBirdsNoGo_lens3to2___closed__0();
lean_mark_persistent(lp_sixbirdsnogo_SixBirdsNoGo_lens3to2___closed__0);
lp_sixbirdsnogo_SixBirdsNoGo_lens3to2___closed__1 = _init_lp_sixbirdsnogo_SixBirdsNoGo_lens3to2___closed__1();
lean_mark_persistent(lp_sixbirdsnogo_SixBirdsNoGo_lens3to2___closed__1);
lp_sixbirdsnogo_SixBirdsNoGo_lens3to2 = _init_lp_sixbirdsnogo_SixBirdsNoGo_lens3to2();
lean_mark_persistent(lp_sixbirdsnogo_SixBirdsNoGo_lens3to2);
return lean_io_result_mk_ok(lean_box(0));
}
#ifdef __cplusplus
}
#endif
