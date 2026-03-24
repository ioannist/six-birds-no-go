// Lean compiler output
// Module: SixBirdsNoGo
// Imports: public import Init public import SixBirdsNoGo.Idempotence public import SixBirdsNoGo.TreeExactness public import SixBirdsNoGo.TreeExactnessExample public import SixBirdsNoGo.ClosedWalkExactness public import SixBirdsNoGo.ClosedWalkExactnessExample public import SixBirdsNoGo.ForestForceBridge public import SixBirdsNoGo.ForestForceBridgeExample public import SixBirdsNoGo.NullForceBridge public import SixBirdsNoGo.NullForceBridgeExample public import SixBirdsNoGo.FiniteLensDefinability public import SixBirdsNoGo.FiniteLensDefinabilityExample public import SixBirdsNoGo.BoundedInterfaceNoLadder public import SixBirdsNoGo.BoundedInterfaceNoLadderExample public import SixBirdsNoGo.ContractionUniqueness public import SixBirdsNoGo.ContractionUniquenessExample public import SixBirdsNoGo.FiniteProbabilityCore public import SixBirdsNoGo.FiniteProbabilityCoreExample public import SixBirdsNoGo.FiniteKLDPI public import SixBirdsNoGo.FiniteKLDPIExample public import SixBirdsNoGo.ArrowDPI public import SixBirdsNoGo.ArrowDPIExample public import SixBirdsNoGo.ProtocolTrap public import SixBirdsNoGo.ProtocolTrapExample public import SixBirdsNoGo.ClosureVariationalCore public import SixBirdsNoGo.ClosureVariationalCoreExample public import SixBirdsNoGo.ClosureDirectPack public import SixBirdsNoGo.ClosureDirectPackExample
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
lean_object* initialize_Init(uint8_t builtin);
lean_object* initialize_sixbirdsnogo_SixBirdsNoGo_Idempotence(uint8_t builtin);
lean_object* initialize_sixbirdsnogo_SixBirdsNoGo_TreeExactness(uint8_t builtin);
lean_object* initialize_sixbirdsnogo_SixBirdsNoGo_TreeExactnessExample(uint8_t builtin);
lean_object* initialize_sixbirdsnogo_SixBirdsNoGo_ClosedWalkExactness(uint8_t builtin);
lean_object* initialize_sixbirdsnogo_SixBirdsNoGo_ClosedWalkExactnessExample(uint8_t builtin);
lean_object* initialize_sixbirdsnogo_SixBirdsNoGo_ForestForceBridge(uint8_t builtin);
lean_object* initialize_sixbirdsnogo_SixBirdsNoGo_ForestForceBridgeExample(uint8_t builtin);
lean_object* initialize_sixbirdsnogo_SixBirdsNoGo_NullForceBridge(uint8_t builtin);
lean_object* initialize_sixbirdsnogo_SixBirdsNoGo_NullForceBridgeExample(uint8_t builtin);
lean_object* initialize_sixbirdsnogo_SixBirdsNoGo_FiniteLensDefinability(uint8_t builtin);
lean_object* initialize_sixbirdsnogo_SixBirdsNoGo_FiniteLensDefinabilityExample(uint8_t builtin);
lean_object* initialize_sixbirdsnogo_SixBirdsNoGo_BoundedInterfaceNoLadder(uint8_t builtin);
lean_object* initialize_sixbirdsnogo_SixBirdsNoGo_BoundedInterfaceNoLadderExample(uint8_t builtin);
lean_object* initialize_sixbirdsnogo_SixBirdsNoGo_ContractionUniqueness(uint8_t builtin);
lean_object* initialize_sixbirdsnogo_SixBirdsNoGo_ContractionUniquenessExample(uint8_t builtin);
lean_object* initialize_sixbirdsnogo_SixBirdsNoGo_FiniteProbabilityCore(uint8_t builtin);
lean_object* initialize_sixbirdsnogo_SixBirdsNoGo_FiniteProbabilityCoreExample(uint8_t builtin);
lean_object* initialize_sixbirdsnogo_SixBirdsNoGo_FiniteKLDPI(uint8_t builtin);
lean_object* initialize_sixbirdsnogo_SixBirdsNoGo_FiniteKLDPIExample(uint8_t builtin);
lean_object* initialize_sixbirdsnogo_SixBirdsNoGo_ArrowDPI(uint8_t builtin);
lean_object* initialize_sixbirdsnogo_SixBirdsNoGo_ArrowDPIExample(uint8_t builtin);
lean_object* initialize_sixbirdsnogo_SixBirdsNoGo_ProtocolTrap(uint8_t builtin);
lean_object* initialize_sixbirdsnogo_SixBirdsNoGo_ProtocolTrapExample(uint8_t builtin);
lean_object* initialize_sixbirdsnogo_SixBirdsNoGo_ClosureVariationalCore(uint8_t builtin);
lean_object* initialize_sixbirdsnogo_SixBirdsNoGo_ClosureVariationalCoreExample(uint8_t builtin);
lean_object* initialize_sixbirdsnogo_SixBirdsNoGo_ClosureDirectPack(uint8_t builtin);
lean_object* initialize_sixbirdsnogo_SixBirdsNoGo_ClosureDirectPackExample(uint8_t builtin);
static bool _G_initialized = false;
LEAN_EXPORT lean_object* initialize_sixbirdsnogo_SixBirdsNoGo(uint8_t builtin) {
lean_object * res;
if (_G_initialized) return lean_io_result_mk_ok(lean_box(0));
_G_initialized = true;
res = initialize_Init(builtin);
if (lean_io_result_is_error(res)) return res;
lean_dec_ref(res);
res = initialize_sixbirdsnogo_SixBirdsNoGo_Idempotence(builtin);
if (lean_io_result_is_error(res)) return res;
lean_dec_ref(res);
res = initialize_sixbirdsnogo_SixBirdsNoGo_TreeExactness(builtin);
if (lean_io_result_is_error(res)) return res;
lean_dec_ref(res);
res = initialize_sixbirdsnogo_SixBirdsNoGo_TreeExactnessExample(builtin);
if (lean_io_result_is_error(res)) return res;
lean_dec_ref(res);
res = initialize_sixbirdsnogo_SixBirdsNoGo_ClosedWalkExactness(builtin);
if (lean_io_result_is_error(res)) return res;
lean_dec_ref(res);
res = initialize_sixbirdsnogo_SixBirdsNoGo_ClosedWalkExactnessExample(builtin);
if (lean_io_result_is_error(res)) return res;
lean_dec_ref(res);
res = initialize_sixbirdsnogo_SixBirdsNoGo_ForestForceBridge(builtin);
if (lean_io_result_is_error(res)) return res;
lean_dec_ref(res);
res = initialize_sixbirdsnogo_SixBirdsNoGo_ForestForceBridgeExample(builtin);
if (lean_io_result_is_error(res)) return res;
lean_dec_ref(res);
res = initialize_sixbirdsnogo_SixBirdsNoGo_NullForceBridge(builtin);
if (lean_io_result_is_error(res)) return res;
lean_dec_ref(res);
res = initialize_sixbirdsnogo_SixBirdsNoGo_NullForceBridgeExample(builtin);
if (lean_io_result_is_error(res)) return res;
lean_dec_ref(res);
res = initialize_sixbirdsnogo_SixBirdsNoGo_FiniteLensDefinability(builtin);
if (lean_io_result_is_error(res)) return res;
lean_dec_ref(res);
res = initialize_sixbirdsnogo_SixBirdsNoGo_FiniteLensDefinabilityExample(builtin);
if (lean_io_result_is_error(res)) return res;
lean_dec_ref(res);
res = initialize_sixbirdsnogo_SixBirdsNoGo_BoundedInterfaceNoLadder(builtin);
if (lean_io_result_is_error(res)) return res;
lean_dec_ref(res);
res = initialize_sixbirdsnogo_SixBirdsNoGo_BoundedInterfaceNoLadderExample(builtin);
if (lean_io_result_is_error(res)) return res;
lean_dec_ref(res);
res = initialize_sixbirdsnogo_SixBirdsNoGo_ContractionUniqueness(builtin);
if (lean_io_result_is_error(res)) return res;
lean_dec_ref(res);
res = initialize_sixbirdsnogo_SixBirdsNoGo_ContractionUniquenessExample(builtin);
if (lean_io_result_is_error(res)) return res;
lean_dec_ref(res);
res = initialize_sixbirdsnogo_SixBirdsNoGo_FiniteProbabilityCore(builtin);
if (lean_io_result_is_error(res)) return res;
lean_dec_ref(res);
res = initialize_sixbirdsnogo_SixBirdsNoGo_FiniteProbabilityCoreExample(builtin);
if (lean_io_result_is_error(res)) return res;
lean_dec_ref(res);
res = initialize_sixbirdsnogo_SixBirdsNoGo_FiniteKLDPI(builtin);
if (lean_io_result_is_error(res)) return res;
lean_dec_ref(res);
res = initialize_sixbirdsnogo_SixBirdsNoGo_FiniteKLDPIExample(builtin);
if (lean_io_result_is_error(res)) return res;
lean_dec_ref(res);
res = initialize_sixbirdsnogo_SixBirdsNoGo_ArrowDPI(builtin);
if (lean_io_result_is_error(res)) return res;
lean_dec_ref(res);
res = initialize_sixbirdsnogo_SixBirdsNoGo_ArrowDPIExample(builtin);
if (lean_io_result_is_error(res)) return res;
lean_dec_ref(res);
res = initialize_sixbirdsnogo_SixBirdsNoGo_ProtocolTrap(builtin);
if (lean_io_result_is_error(res)) return res;
lean_dec_ref(res);
res = initialize_sixbirdsnogo_SixBirdsNoGo_ProtocolTrapExample(builtin);
if (lean_io_result_is_error(res)) return res;
lean_dec_ref(res);
res = initialize_sixbirdsnogo_SixBirdsNoGo_ClosureVariationalCore(builtin);
if (lean_io_result_is_error(res)) return res;
lean_dec_ref(res);
res = initialize_sixbirdsnogo_SixBirdsNoGo_ClosureVariationalCoreExample(builtin);
if (lean_io_result_is_error(res)) return res;
lean_dec_ref(res);
res = initialize_sixbirdsnogo_SixBirdsNoGo_ClosureDirectPack(builtin);
if (lean_io_result_is_error(res)) return res;
lean_dec_ref(res);
res = initialize_sixbirdsnogo_SixBirdsNoGo_ClosureDirectPackExample(builtin);
if (lean_io_result_is_error(res)) return res;
lean_dec_ref(res);
return lean_io_result_mk_ok(lean_box(0));
}
#ifdef __cplusplus
}
#endif
