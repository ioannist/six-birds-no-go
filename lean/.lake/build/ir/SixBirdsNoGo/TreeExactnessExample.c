// Lean compiler output
// Module: SixBirdsNoGo.TreeExactnessExample
// Imports: public import Init public import SixBirdsNoGo.TreeExactness
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
static lean_object* lp_sixbirdsnogo_SixBirdsNoGo_exampleTree___closed__3;
static lean_object* lp_sixbirdsnogo_SixBirdsNoGo_pToLeaf___closed__0;
static lean_object* lp_sixbirdsnogo_SixBirdsNoGo_exampleTree___closed__0;
static lean_object* lp_sixbirdsnogo_SixBirdsNoGo_childA___closed__0;
LEAN_EXPORT lean_object* lp_sixbirdsnogo_SixBirdsNoGo_pToLeaf;
static lean_object* lp_sixbirdsnogo_SixBirdsNoGo_exampleTree___closed__6;
LEAN_EXPORT lean_object* lp_sixbirdsnogo_SixBirdsNoGo_childB;
LEAN_EXPORT lean_object* lp_sixbirdsnogo_SixBirdsNoGo_exampleTree;
lean_object* lean_nat_to_int(lean_object*);
static lean_object* lp_sixbirdsnogo_SixBirdsNoGo_exampleTree___closed__5;
static lean_object* lp_sixbirdsnogo_SixBirdsNoGo_exampleTree___closed__4;
static lean_object* lp_sixbirdsnogo_SixBirdsNoGo_pToChildA___closed__0;
static lean_object* lp_sixbirdsnogo_SixBirdsNoGo_childA___closed__2;
static lean_object* lp_sixbirdsnogo_SixBirdsNoGo_childA___closed__1;
LEAN_EXPORT lean_object* lp_sixbirdsnogo_SixBirdsNoGo_pToChildA;
static lean_object* lp_sixbirdsnogo_SixBirdsNoGo_exampleTree___closed__2;
static lean_object* lp_sixbirdsnogo_SixBirdsNoGo_leaf___closed__0;
static lean_object* lp_sixbirdsnogo_SixBirdsNoGo_exampleTree___closed__7;
LEAN_EXPORT lean_object* lp_sixbirdsnogo_SixBirdsNoGo_childA;
LEAN_EXPORT lean_object* lp_sixbirdsnogo_SixBirdsNoGo_leaf;
static lean_object* lp_sixbirdsnogo_SixBirdsNoGo_childA___closed__3;
static lean_object* lp_sixbirdsnogo_SixBirdsNoGo_exampleTree___closed__1;
lean_object* lean_int_neg(lean_object*);
static lean_object* _init_lp_sixbirdsnogo_SixBirdsNoGo_leaf___closed__0() {
_start:
{
lean_object* x_1; lean_object* x_2; 
x_1 = lean_box(0);
x_2 = lean_alloc_ctor(0, 1, 0);
lean_ctor_set(x_2, 0, x_1);
return x_2;
}
}
static lean_object* _init_lp_sixbirdsnogo_SixBirdsNoGo_leaf() {
_start:
{
lean_object* x_1; 
x_1 = lp_sixbirdsnogo_SixBirdsNoGo_leaf___closed__0;
return x_1;
}
}
static lean_object* _init_lp_sixbirdsnogo_SixBirdsNoGo_childA___closed__0() {
_start:
{
lean_object* x_1; lean_object* x_2; 
x_1 = lean_unsigned_to_nat(5u);
x_2 = lean_nat_to_int(x_1);
return x_2;
}
}
static lean_object* _init_lp_sixbirdsnogo_SixBirdsNoGo_childA___closed__1() {
_start:
{
lean_object* x_1; lean_object* x_2; lean_object* x_3; 
x_1 = lp_sixbirdsnogo_SixBirdsNoGo_leaf;
x_2 = lp_sixbirdsnogo_SixBirdsNoGo_childA___closed__0;
x_3 = lean_alloc_ctor(0, 2, 0);
lean_ctor_set(x_3, 0, x_2);
lean_ctor_set(x_3, 1, x_1);
return x_3;
}
}
static lean_object* _init_lp_sixbirdsnogo_SixBirdsNoGo_childA___closed__2() {
_start:
{
lean_object* x_1; lean_object* x_2; lean_object* x_3; 
x_1 = lean_box(0);
x_2 = lp_sixbirdsnogo_SixBirdsNoGo_childA___closed__1;
x_3 = lean_alloc_ctor(1, 2, 0);
lean_ctor_set(x_3, 0, x_2);
lean_ctor_set(x_3, 1, x_1);
return x_3;
}
}
static lean_object* _init_lp_sixbirdsnogo_SixBirdsNoGo_childA___closed__3() {
_start:
{
lean_object* x_1; lean_object* x_2; 
x_1 = lp_sixbirdsnogo_SixBirdsNoGo_childA___closed__2;
x_2 = lean_alloc_ctor(0, 1, 0);
lean_ctor_set(x_2, 0, x_1);
return x_2;
}
}
static lean_object* _init_lp_sixbirdsnogo_SixBirdsNoGo_childA() {
_start:
{
lean_object* x_1; 
x_1 = lp_sixbirdsnogo_SixBirdsNoGo_childA___closed__3;
return x_1;
}
}
static lean_object* _init_lp_sixbirdsnogo_SixBirdsNoGo_childB() {
_start:
{
lean_object* x_1; 
x_1 = lp_sixbirdsnogo_SixBirdsNoGo_leaf___closed__0;
return x_1;
}
}
static lean_object* _init_lp_sixbirdsnogo_SixBirdsNoGo_exampleTree___closed__0() {
_start:
{
lean_object* x_1; lean_object* x_2; 
x_1 = lean_unsigned_to_nat(3u);
x_2 = lean_nat_to_int(x_1);
return x_2;
}
}
static lean_object* _init_lp_sixbirdsnogo_SixBirdsNoGo_exampleTree___closed__1() {
_start:
{
lean_object* x_1; lean_object* x_2; lean_object* x_3; 
x_1 = lp_sixbirdsnogo_SixBirdsNoGo_childA;
x_2 = lp_sixbirdsnogo_SixBirdsNoGo_exampleTree___closed__0;
x_3 = lean_alloc_ctor(0, 2, 0);
lean_ctor_set(x_3, 0, x_2);
lean_ctor_set(x_3, 1, x_1);
return x_3;
}
}
static lean_object* _init_lp_sixbirdsnogo_SixBirdsNoGo_exampleTree___closed__2() {
_start:
{
lean_object* x_1; lean_object* x_2; 
x_1 = lean_unsigned_to_nat(2u);
x_2 = lean_nat_to_int(x_1);
return x_2;
}
}
static lean_object* _init_lp_sixbirdsnogo_SixBirdsNoGo_exampleTree___closed__3() {
_start:
{
lean_object* x_1; lean_object* x_2; 
x_1 = lp_sixbirdsnogo_SixBirdsNoGo_exampleTree___closed__2;
x_2 = lean_int_neg(x_1);
return x_2;
}
}
static lean_object* _init_lp_sixbirdsnogo_SixBirdsNoGo_exampleTree___closed__4() {
_start:
{
lean_object* x_1; lean_object* x_2; lean_object* x_3; 
x_1 = lp_sixbirdsnogo_SixBirdsNoGo_childB;
x_2 = lp_sixbirdsnogo_SixBirdsNoGo_exampleTree___closed__3;
x_3 = lean_alloc_ctor(0, 2, 0);
lean_ctor_set(x_3, 0, x_2);
lean_ctor_set(x_3, 1, x_1);
return x_3;
}
}
static lean_object* _init_lp_sixbirdsnogo_SixBirdsNoGo_exampleTree___closed__5() {
_start:
{
lean_object* x_1; lean_object* x_2; lean_object* x_3; 
x_1 = lean_box(0);
x_2 = lp_sixbirdsnogo_SixBirdsNoGo_exampleTree___closed__4;
x_3 = lean_alloc_ctor(1, 2, 0);
lean_ctor_set(x_3, 0, x_2);
lean_ctor_set(x_3, 1, x_1);
return x_3;
}
}
static lean_object* _init_lp_sixbirdsnogo_SixBirdsNoGo_exampleTree___closed__6() {
_start:
{
lean_object* x_1; lean_object* x_2; lean_object* x_3; 
x_1 = lp_sixbirdsnogo_SixBirdsNoGo_exampleTree___closed__5;
x_2 = lp_sixbirdsnogo_SixBirdsNoGo_exampleTree___closed__1;
x_3 = lean_alloc_ctor(1, 2, 0);
lean_ctor_set(x_3, 0, x_2);
lean_ctor_set(x_3, 1, x_1);
return x_3;
}
}
static lean_object* _init_lp_sixbirdsnogo_SixBirdsNoGo_exampleTree___closed__7() {
_start:
{
lean_object* x_1; lean_object* x_2; 
x_1 = lp_sixbirdsnogo_SixBirdsNoGo_exampleTree___closed__6;
x_2 = lean_alloc_ctor(0, 1, 0);
lean_ctor_set(x_2, 0, x_1);
return x_2;
}
}
static lean_object* _init_lp_sixbirdsnogo_SixBirdsNoGo_exampleTree() {
_start:
{
lean_object* x_1; 
x_1 = lp_sixbirdsnogo_SixBirdsNoGo_exampleTree___closed__7;
return x_1;
}
}
static lean_object* _init_lp_sixbirdsnogo_SixBirdsNoGo_pToChildA___closed__0() {
_start:
{
lean_object* x_1; lean_object* x_2; lean_object* x_3; lean_object* x_4; lean_object* x_5; 
x_1 = lp_sixbirdsnogo_SixBirdsNoGo_exampleTree___closed__0;
x_2 = lean_box(0);
x_3 = lp_sixbirdsnogo_SixBirdsNoGo_childA;
x_4 = lp_sixbirdsnogo_SixBirdsNoGo_exampleTree;
x_5 = lean_alloc_ctor(1, 4, 0);
lean_ctor_set(x_5, 0, x_4);
lean_ctor_set(x_5, 1, x_3);
lean_ctor_set(x_5, 2, x_2);
lean_ctor_set(x_5, 3, x_1);
return x_5;
}
}
static lean_object* _init_lp_sixbirdsnogo_SixBirdsNoGo_pToChildA() {
_start:
{
lean_object* x_1; 
x_1 = lp_sixbirdsnogo_SixBirdsNoGo_pToChildA___closed__0;
return x_1;
}
}
static lean_object* _init_lp_sixbirdsnogo_SixBirdsNoGo_pToLeaf___closed__0() {
_start:
{
lean_object* x_1; lean_object* x_2; lean_object* x_3; lean_object* x_4; lean_object* x_5; 
x_1 = lp_sixbirdsnogo_SixBirdsNoGo_childA___closed__0;
x_2 = lp_sixbirdsnogo_SixBirdsNoGo_pToChildA;
x_3 = lp_sixbirdsnogo_SixBirdsNoGo_leaf;
x_4 = lp_sixbirdsnogo_SixBirdsNoGo_childA;
x_5 = lean_alloc_ctor(1, 4, 0);
lean_ctor_set(x_5, 0, x_4);
lean_ctor_set(x_5, 1, x_3);
lean_ctor_set(x_5, 2, x_2);
lean_ctor_set(x_5, 3, x_1);
return x_5;
}
}
static lean_object* _init_lp_sixbirdsnogo_SixBirdsNoGo_pToLeaf() {
_start:
{
lean_object* x_1; 
x_1 = lp_sixbirdsnogo_SixBirdsNoGo_pToLeaf___closed__0;
return x_1;
}
}
lean_object* initialize_Init(uint8_t builtin);
lean_object* initialize_sixbirdsnogo_SixBirdsNoGo_TreeExactness(uint8_t builtin);
static bool _G_initialized = false;
LEAN_EXPORT lean_object* initialize_sixbirdsnogo_SixBirdsNoGo_TreeExactnessExample(uint8_t builtin) {
lean_object * res;
if (_G_initialized) return lean_io_result_mk_ok(lean_box(0));
_G_initialized = true;
res = initialize_Init(builtin);
if (lean_io_result_is_error(res)) return res;
lean_dec_ref(res);
res = initialize_sixbirdsnogo_SixBirdsNoGo_TreeExactness(builtin);
if (lean_io_result_is_error(res)) return res;
lean_dec_ref(res);
lp_sixbirdsnogo_SixBirdsNoGo_leaf___closed__0 = _init_lp_sixbirdsnogo_SixBirdsNoGo_leaf___closed__0();
lean_mark_persistent(lp_sixbirdsnogo_SixBirdsNoGo_leaf___closed__0);
lp_sixbirdsnogo_SixBirdsNoGo_leaf = _init_lp_sixbirdsnogo_SixBirdsNoGo_leaf();
lean_mark_persistent(lp_sixbirdsnogo_SixBirdsNoGo_leaf);
lp_sixbirdsnogo_SixBirdsNoGo_childA___closed__0 = _init_lp_sixbirdsnogo_SixBirdsNoGo_childA___closed__0();
lean_mark_persistent(lp_sixbirdsnogo_SixBirdsNoGo_childA___closed__0);
lp_sixbirdsnogo_SixBirdsNoGo_childA___closed__1 = _init_lp_sixbirdsnogo_SixBirdsNoGo_childA___closed__1();
lean_mark_persistent(lp_sixbirdsnogo_SixBirdsNoGo_childA___closed__1);
lp_sixbirdsnogo_SixBirdsNoGo_childA___closed__2 = _init_lp_sixbirdsnogo_SixBirdsNoGo_childA___closed__2();
lean_mark_persistent(lp_sixbirdsnogo_SixBirdsNoGo_childA___closed__2);
lp_sixbirdsnogo_SixBirdsNoGo_childA___closed__3 = _init_lp_sixbirdsnogo_SixBirdsNoGo_childA___closed__3();
lean_mark_persistent(lp_sixbirdsnogo_SixBirdsNoGo_childA___closed__3);
lp_sixbirdsnogo_SixBirdsNoGo_childA = _init_lp_sixbirdsnogo_SixBirdsNoGo_childA();
lean_mark_persistent(lp_sixbirdsnogo_SixBirdsNoGo_childA);
lp_sixbirdsnogo_SixBirdsNoGo_childB = _init_lp_sixbirdsnogo_SixBirdsNoGo_childB();
lean_mark_persistent(lp_sixbirdsnogo_SixBirdsNoGo_childB);
lp_sixbirdsnogo_SixBirdsNoGo_exampleTree___closed__0 = _init_lp_sixbirdsnogo_SixBirdsNoGo_exampleTree___closed__0();
lean_mark_persistent(lp_sixbirdsnogo_SixBirdsNoGo_exampleTree___closed__0);
lp_sixbirdsnogo_SixBirdsNoGo_exampleTree___closed__1 = _init_lp_sixbirdsnogo_SixBirdsNoGo_exampleTree___closed__1();
lean_mark_persistent(lp_sixbirdsnogo_SixBirdsNoGo_exampleTree___closed__1);
lp_sixbirdsnogo_SixBirdsNoGo_exampleTree___closed__2 = _init_lp_sixbirdsnogo_SixBirdsNoGo_exampleTree___closed__2();
lean_mark_persistent(lp_sixbirdsnogo_SixBirdsNoGo_exampleTree___closed__2);
lp_sixbirdsnogo_SixBirdsNoGo_exampleTree___closed__3 = _init_lp_sixbirdsnogo_SixBirdsNoGo_exampleTree___closed__3();
lean_mark_persistent(lp_sixbirdsnogo_SixBirdsNoGo_exampleTree___closed__3);
lp_sixbirdsnogo_SixBirdsNoGo_exampleTree___closed__4 = _init_lp_sixbirdsnogo_SixBirdsNoGo_exampleTree___closed__4();
lean_mark_persistent(lp_sixbirdsnogo_SixBirdsNoGo_exampleTree___closed__4);
lp_sixbirdsnogo_SixBirdsNoGo_exampleTree___closed__5 = _init_lp_sixbirdsnogo_SixBirdsNoGo_exampleTree___closed__5();
lean_mark_persistent(lp_sixbirdsnogo_SixBirdsNoGo_exampleTree___closed__5);
lp_sixbirdsnogo_SixBirdsNoGo_exampleTree___closed__6 = _init_lp_sixbirdsnogo_SixBirdsNoGo_exampleTree___closed__6();
lean_mark_persistent(lp_sixbirdsnogo_SixBirdsNoGo_exampleTree___closed__6);
lp_sixbirdsnogo_SixBirdsNoGo_exampleTree___closed__7 = _init_lp_sixbirdsnogo_SixBirdsNoGo_exampleTree___closed__7();
lean_mark_persistent(lp_sixbirdsnogo_SixBirdsNoGo_exampleTree___closed__7);
lp_sixbirdsnogo_SixBirdsNoGo_exampleTree = _init_lp_sixbirdsnogo_SixBirdsNoGo_exampleTree();
lean_mark_persistent(lp_sixbirdsnogo_SixBirdsNoGo_exampleTree);
lp_sixbirdsnogo_SixBirdsNoGo_pToChildA___closed__0 = _init_lp_sixbirdsnogo_SixBirdsNoGo_pToChildA___closed__0();
lean_mark_persistent(lp_sixbirdsnogo_SixBirdsNoGo_pToChildA___closed__0);
lp_sixbirdsnogo_SixBirdsNoGo_pToChildA = _init_lp_sixbirdsnogo_SixBirdsNoGo_pToChildA();
lean_mark_persistent(lp_sixbirdsnogo_SixBirdsNoGo_pToChildA);
lp_sixbirdsnogo_SixBirdsNoGo_pToLeaf___closed__0 = _init_lp_sixbirdsnogo_SixBirdsNoGo_pToLeaf___closed__0();
lean_mark_persistent(lp_sixbirdsnogo_SixBirdsNoGo_pToLeaf___closed__0);
lp_sixbirdsnogo_SixBirdsNoGo_pToLeaf = _init_lp_sixbirdsnogo_SixBirdsNoGo_pToLeaf();
lean_mark_persistent(lp_sixbirdsnogo_SixBirdsNoGo_pToLeaf);
return lean_io_result_mk_ok(lean_box(0));
}
#ifdef __cplusplus
}
#endif
