import type { EmployeeDTO } from "@/api/costEngine";
import type {
  Advance,
  DocumentStatus,
  EmployeeDocument,
  EmployeeRecord,
  EmployeeStatus,
  InternalAlert,
  PaymentRun,
  PaymentStatus,
} from "@/lib/employeeRecordsData";
import {
  DOCUMENT_TYPE_LABELS,
  getMonthlyAttendance,
} from "@/lib/employeeRecordsData";

const DEMO_NAMES = [
  "Ion Popescu",
  "Mihai Ionescu",
  "Andrei Vasile",
  "Elena Dumitrescu",
  "Sorin Marin",
  "Dana Gheorghe",
];

export function mapOperationalEmployeeToRecord(emp: EmployeeDTO, index: number): EmployeeRecord {
  const statusRaw = (emp.status ?? "active").toLowerCase();
  let status: EmployeeStatus = "activ";
  if (statusRaw === "inactive") status = "inactiv";
  else if (statusRaw === "plecat" || statusRaw === "terminated") status = "plecat";

  const skills = Array.isArray(emp.skills) ? emp.skills : [];
  const department = emp.department?.trim() || "Producție";
  const role = emp.role?.trim() || "Operator";

  return {
    id: String(emp.id),
    name: emp.name,
    functie: role,
    departament: department,
    statiePrincipala: skills[0] ?? department,
    status,
    dataAngajarii: emp.data_angajare ?? "2020-01-01",
    telefon: "",
    email: "",
    observatii: emp.observatii ?? "",
    sumaLunaraInterna: emp.cost_lunar_firma ?? 4000 + (index % 6) * 350,
    skills,
  };
}

export function buildEmployeeRecordsFromOperational(employees: EmployeeDTO[]): EmployeeRecord[] {
  return employees.map((emp, index) => mapOperationalEmployeeToRecord(emp, index));
}

export function buildDemoDocumentsForEmployees(employees: EmployeeRecord[]): EmployeeDocument[] {
  const medicinaStatuses: DocumentStatus[] = ["valid", "expira_curand", "expirat", "valid", "lipsa", "valid"];

  return employees.flatMap((emp, index) => {
    const medicinaStatus = medicinaStatuses[index % medicinaStatuses.length];
    const fisaStatus: DocumentStatus = index % 4 === 3 ? "lipsa" : "valid";
    const baseId = `doc-${emp.id}`;

    return [
      {
        id: `${baseId}-contract`,
        employeeId: emp.id,
        tip: "contract_munca",
        tipLabel: DOCUMENT_TYPE_LABELS.contract_munca,
        dataEmitere: emp.dataAngajarii,
        dataExpirare: null,
        status: "valid",
        observatii: "Contract demonstrativ — evidență internă",
      },
      {
        id: `${baseId}-fisa`,
        employeeId: emp.id,
        tip: "fisa_post",
        tipLabel: DOCUMENT_TYPE_LABELS.fisa_post,
        dataEmitere: emp.dataAngajarii,
        dataExpirare: null,
        status: fisaStatus,
        observatii: fisaStatus === "lipsa" ? "Fișă post lipsă — de generat" : "",
      },
      {
        id: `${baseId}-medicina`,
        employeeId: emp.id,
        tip: "medicina_muncii",
        tipLabel: DOCUMENT_TYPE_LABELS.medicina_muncii,
        dataEmitere: "2024-01-15",
        dataExpirare: medicinaStatus === "expirat" ? "2024-08-10" : "2025-06-15",
        status: medicinaStatus,
        observatii:
          medicinaStatus === "expirat"
            ? "EXPIRAT — necesită reînnoire urgentă"
            : medicinaStatus === "expira_curand"
              ? "Expiră în 30 zile"
              : "",
      },
    ];
  });
}

export function buildDemoAdvancesForEmployees(employees: EmployeeRecord[]): Advance[] {
  const advances: Advance[] = [];

  employees.forEach((emp, index) => {
    if (index % 3 === 0) {
      advances.push({
        id: `adv-${emp.id}-avans`,
        employeeId: emp.id,
        employeeName: emp.name,
        tip: "avans",
        suma: 300 + (index % 4) * 100,
        dataAcordare: "2025-06-05",
        status: "activ",
        observatii: "Avans demonstrativ pe angajat live",
      });
    }
    if (index % 4 === 1) {
      advances.push({
        id: `adv-${emp.id}-imprumut`,
        employeeId: emp.id,
        employeeName: emp.name,
        tip: "imprumut",
        suma: 2000 + index * 200,
        dataAcordare: "2025-03-01",
        nrRate: 6,
        rataLunara: 400,
        soldRamas: 1200 + index * 100,
        dataInceput: "2025-03-15",
        status: "activ",
        observatii: "Împrumut demonstrativ",
      });
    }
    if (index % 5 === 2) {
      advances.push({
        id: `adv-${emp.id}-retinere`,
        employeeId: emp.id,
        employeeName: emp.name,
        tip: "retinere",
        suma: 150 + index * 25,
        dataAcordare: "2025-06-01",
        motiv: "Reținere demonstrativă",
        lunaAplicare: "2025-06",
        status: "activ",
        observatii: "Reținere unică demonstrativă",
      });
    }
  });

  return advances;
}

export function buildDemoAlertsForEmployees(employees: EmployeeRecord[]): InternalAlert[] {
  const alerts: InternalAlert[] = [];

  employees.forEach((emp, index) => {
    if (index % 3 === 0) {
      alerts.push({
        id: `alert-${emp.id}-medicina`,
        employeeId: emp.id,
        employeeName: emp.name,
        type: "medicina_muncii_expira",
        message: `Medicina muncii — verificare demonstrativă pentru ${emp.name}`,
        severity: index % 6 === 0 ? "error" : "warning",
        date: "2025-06-01",
      });
    }
    if (index % 4 === 1) {
      alerts.push({
        id: `alert-${emp.id}-datorie`,
        employeeId: emp.id,
        employeeName: emp.name,
        type: "datorie_activa",
        message: "Datorie/împrumut demonstrativ activ pe angajat live",
        severity: "info",
        date: "2025-06-01",
      });
    }
    if (index % 5 === 2) {
      alerts.push({
        id: `alert-${emp.id}-doc`,
        employeeId: emp.id,
        employeeName: emp.name,
        type: "document_lipsa",
        message: "Document intern lipsă — demo",
        severity: "warning",
        date: "2025-06-01",
      });
    }
  });

  alerts.push({
    id: "alert-global-plata",
    employeeId: "",
    employeeName: "",
    type: "data_plata_aproape",
    message: "Data de plată 15 se apropie — verifică calculele",
    severity: "info",
    date: "2025-06-12",
  });

  if (employees.length > 2) {
    const target = employees[2];
    alerts.push({
      id: "alert-global-neconfirmata",
      employeeId: target.id,
      employeeName: target.name,
      type: "plata_neconfirmata",
      message: "Plata pe 15 pregătită dar nemarcată ca plătită (demo)",
      severity: "warning",
      date: "2025-06-15",
    });
  }

  return alerts;
}

export function generatePaymentRunForEmployees(
  employees: EmployeeRecord[],
  advances: Advance[],
  month: string,
  dataPlata: "15" | "30"
): PaymentRun[] {
  return employees
    .filter((e) => e.status === "activ")
    .map((emp, index) => {
      const attendance = getMonthlyAttendance(emp.id, month);
      const empAdvances = advances.filter((a) => a.employeeId === emp.id && a.status === "activ");

      const transaTeorica = Math.round(emp.sumaLunaraInterna * 0.5);
      const zileLipsa = attendance.zileLipsa + attendance.zileNemotivat;
      const costZi =
        attendance.zileLucratoare > 0
          ? Math.round(emp.sumaLunaraInterna / attendance.zileLucratoare)
          : 0;
      const deducereZileLipsa = zileLipsa * costZi;
      const costOra =
        attendance.zileLucratoare > 0
          ? Math.round(emp.sumaLunaraInterna / (attendance.zileLucratoare * 8))
          : 0;
      const valorOreSuplimentare = attendance.oreSuplimentare * costOra * 1.5;

      const totalAvansuri = empAdvances
        .filter((a) => a.tip === "avans")
        .reduce((s, a) => s + a.suma, 0);
      const totalRate = empAdvances
        .filter((a) => a.tip === "imprumut")
        .reduce((s, a) => s + (a.rataLunara || 0), 0);
      const alteRetineri = empAdvances
        .filter((a) => a.tip === "retinere")
        .reduce((s, a) => s + a.suma, 0);

      const bonusuri = index % 3 === 0 ? 200 : index % 5 === 1 ? 150 : 0;

      const totalDeDat = Math.max(
        0,
        transaTeorica -
          deducereZileLipsa +
          Math.round(valorOreSuplimentare) +
          bonusuri -
          totalAvansuri -
          totalRate -
          alteRetineri
      );

      let status: PaymentStatus = "de_calculat";
      if (dataPlata === "15") {
        status = index % 2 === 0 ? "platit" : "pregatit_plata";
      }

      return {
        id: `pay-${emp.id}-${month}-${dataPlata}`,
        employeeId: emp.id,
        employeeName: emp.name,
        month,
        dataPlata,
        sumaLunaraInterna: emp.sumaLunaraInterna,
        transaTeorica,
        zileLipsa,
        deducereZileLipsa,
        oreSuplimentare: attendance.oreSuplimentare,
        valorOreSuplimentare: Math.round(valorOreSuplimentare),
        bonusuri,
        avansuri: totalAvansuri,
        rateDatorii: totalRate,
        alteRetineri,
        totalDeDat,
        status,
      };
    });
}

export function containsLegacyDemoNames(employees: EmployeeRecord[]): boolean {
  return employees.some((e) => DEMO_NAMES.includes(e.name));
}
