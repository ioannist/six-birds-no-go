// Lean compiler output
// Module: SixBirdsNoGo.ProtocolTrap
// Imports: public import Init public import SixBirdsNoGo.ArrowDPI public import SixBirdsNoGo.FiniteProbabilityCore
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
LEAN_EXPORT lean_object* lp_sixbirdsnogo_SixBirdsNoGo_honestObservedLiftedPathLaw___boxed(lean_object*, lean_object*, lean_object*, lean_object*, lean_object*);
LEAN_EXPORT lean_object* lp_sixbirdsnogo_SixBirdsNoGo_liftedPathLaw___redArg(lean_object*, lean_object*);
LEAN_EXPORT lean_object* lp_sixbirdsnogo_SixBirdsNoGo_liftedPathLaw(lean_object*, lean_object*, lean_object*);
lean_object* lp_sixbirdsnogo_SixBirdsNoGo_pushforwardPathLaw___redArg(lean_object*, lean_object*, lean_object*);
lean_object* lp_sixbirdsnogo_SixBirdsNoGo_pathLaw___redArg(lean_object*, lean_object*, lean_object*);
LEAN_EXPORT lean_object* lp_sixbirdsnogo_SixBirdsNoGo_liftedPathLaw___redArg___boxed(lean_object*, lean_object*);
LEAN_EXPORT lean_object* lp_sixbirdsnogo_SixBirdsNoGo_honestObservedLiftedPathLaw___redArg(lean_object*, lean_object*, lean_object*);
LEAN_EXPORT lean_object* lp_sixbirdsnogo_SixBirdsNoGo_liftedPathLaw___boxed(lean_object*, lean_object*, lean_object*);
LEAN_EXPORT lean_object* lp_sixbirdsnogo_SixBirdsNoGo_honestObservedLiftedPathLaw(lean_object*, lean_object*, lean_object*, lean_object*, lean_object*);
LEAN_EXPORT lean_object* lp_sixbirdsnogo_SixBirdsNoGo_liftedPathLaw___redArg(lean_object* x_1, lean_object* x_2) {
_start:
{
lean_object* x_3; lean_object* x_4; lean_object* x_5; 
x_3 = lean_ctor_get(x_1, 0);
lean_inc(x_3);
x_4 = lean_ctor_get(x_1, 1);
lean_inc_ref(x_4);
lean_dec_ref(x_1);
x_5 = lp_sixbirdsnogo_SixBirdsNoGo_pathLaw___redArg(x_3, x_4, x_2);
lean_dec(x_3);
return x_5;
}
}
LEAN_EXPORT lean_object* lp_sixbirdsnogo_SixBirdsNoGo_liftedPathLaw___redArg___boxed(lean_object* x_1, lean_object* x_2) {
_start:
{
lean_object* x_3; 
x_3 = lp_sixbirdsnogo_SixBirdsNoGo_liftedPathLaw___redArg(x_1, x_2);
lean_dec(x_2);
return x_3;
}
}
LEAN_EXPORT lean_object* lp_sixbirdsnogo_SixBirdsNoGo_liftedPathLaw(lean_object* x_1, lean_object* x_2, lean_object* x_3) {
_start:
{
lean_object* x_4; 
x_4 = lp_sixbirdsnogo_SixBirdsNoGo_liftedPathLaw___redArg(x_2, x_3);
return x_4;
}
}
LEAN_EXPORT lean_object* lp_sixbirdsnogo_SixBirdsNoGo_liftedPathLaw___boxed(lean_object* x_1, lean_object* x_2, lean_object* x_3) {
_start:
{
lean_object* x_4; 
x_4 = lp_sixbirdsnogo_SixBirdsNoGo_liftedPathLaw(x_1, x_2, x_3);
lean_dec(x_3);
lean_dec(x_1);
return x_4;
}
}
LEAN_EXPORT lean_object* lp_sixbirdsnogo_SixBirdsNoGo_honestObservedLiftedPathLaw___redArg(lean_object* x_1, lean_object* x_2, lean_object* x_3) {
_start:
{
lean_object* x_4; lean_object* x_5; 
x_4 = lp_sixbirdsnogo_SixBirdsNoGo_liftedPathLaw___redArg(x_2, x_3);
x_5 = lp_sixbirdsnogo_SixBirdsNoGo_pushforwardPathLaw___redArg(x_3, x_1, x_4);
return x_5;
}
}
LEAN_EXPORT lean_object* lp_sixbirdsnogo_SixBirdsNoGo_honestObservedLiftedPathLaw(lean_object* x_1, lean_object* x_2, lean_object* x_3, lean_object* x_4, lean_object* x_5) {
_start:
{
lean_object* x_6; 
x_6 = lp_sixbirdsnogo_SixBirdsNoGo_honestObservedLiftedPathLaw___redArg(x_3, x_4, x_5);
return x_6;
}
}
LEAN_EXPORT lean_object* lp_sixbirdsnogo_SixBirdsNoGo_honestObservedLiftedPathLaw___boxed(lean_object* x_1, lean_object* x_2, lean_object* x_3, lean_object* x_4, lean_object* x_5) {
_start:
{
lean_object* x_6; 
x_6 = lp_sixbirdsnogo_SixBirdsNoGo_honestObservedLiftedPathLaw(x_1, x_2, x_3, x_4, x_5);
lean_dec(x_2);
lean_dec(x_1);
return x_6;
}
}
lean_object* initialize_Init(uint8_t builtin);
lean_object* initialize_sixbirdsnogo_SixBirdsNoGo_ArrowDPI(uint8_t builtin);
lean_object* initialize_sixbirdsnogo_SixBirdsNoGo_FiniteProbabilityCore(uint8_t builtin);
static bool _G_initialized = false;
LEAN_EXPORT lean_object* initialize_sixbirdsnogo_SixBirdsNoGo_ProtocolTrap(uint8_t builtin) {
lean_object * res;
if (_G_initialized) return lean_io_result_mk_ok(lean_box(0));
_G_initialized = true;
res = initialize_Init(builtin);
if (lean_io_result_is_error(res)) return res;
lean_dec_ref(res);
res = initialize_sixbirdsnogo_SixBirdsNoGo_ArrowDPI(builtin);
if (lean_io_result_is_error(res)) return res;
lean_dec_ref(res);
res = initialize_sixbirdsnogo_SixBirdsNoGo_FiniteProbabilityCore(builtin);
if (lean_io_result_is_error(res)) return res;
lean_dec_ref(res);
return lean_io_result_mk_ok(lean_box(0));
}
#ifdef __cplusplus
}
#endif
