import { Navigate, useLocation } from "react-router-dom";
import { PRODUCT_SYSTEM_PRODUCTS_PATH } from "./productSystemShellConfig";

/** Preserves query string (e.g. Intake ?template= deep links). */
export default function ProductSystemIndexRedirect() {
  const location = useLocation();
  return (
    <Navigate
      to={{ pathname: PRODUCT_SYSTEM_PRODUCTS_PATH, search: location.search }}
      replace
    />
  );
}
