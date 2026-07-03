import { getAPIBaseURL } from '../lib/config';

const getAPIBase = () => `${getAPIBaseURL()}/api/v1`;

export interface ProductFamily {
  id: number;
  family_id: string;
  label: string;
  category?: string | null;
  active: boolean;
  default_template_id?: number | null;
  description?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface ProductFamilyListResponse {
  items: ProductFamily[];
  total: number;
  skip: number;
  limit: number;
}

export interface ProductFamilyInput {
  family_id: string;
  label: string;
  category?: string | null;
  active?: boolean;
  default_template_id?: number | null;
  description?: string | null;
}

export interface ResolveTemplateResponse {
  status: 'ok' | 'not_found' | 'ambiguous';
  message: string;
  template: {
    id: number;
    template_code: string;
    family_id: string;
    family_name?: string | null;
  } | null;
  candidates: Array<{
    id: number;
    template_code: string;
    family_id: string;
    family_name?: string | null;
  }>;
}

async function handle<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const txt = await res.text().catch(() => '');
    throw new Error(`Request failed (${res.status}): ${txt}`);
  }
  return (await res.json()) as T;
}

export const productFamiliesApi = {
  async list(params?: {
    skip?: number;
    limit?: number;
    query?: Record<string, unknown>;
    sort?: string;
  }): Promise<ProductFamilyListResponse> {
    const search = new URLSearchParams();
    if (params?.skip !== undefined) search.set('skip', String(params.skip));
    if (params?.limit !== undefined) search.set('limit', String(params.limit));
    if (params?.query) search.set('query', JSON.stringify(params.query));
    if (params?.sort) search.set('sort', params.sort);
    const qs = search.toString();
    const url = `${getAPIBase()}/entities/product-families${qs ? `?${qs}` : ''}`;
    const res = await fetch(url, { credentials: 'include' });
    return handle<ProductFamilyListResponse>(res);
  },

  async getById(id: number): Promise<ProductFamily> {
    const res = await fetch(
      `${getAPIBase()}/entities/product-families/${id}`,
      { credentials: 'include' }
    );
    return handle<ProductFamily>(res);
  },

  async getByFamilyId(familyId: string): Promise<ProductFamily> {
    const res = await fetch(
      `${getAPIBase()}/entities/product-families/by-family-id/${encodeURIComponent(familyId)}`,
      { credentials: 'include' }
    );
    return handle<ProductFamily>(res);
  },

  async resolveTemplate(familyId: string): Promise<ResolveTemplateResponse> {
    const res = await fetch(
      `${getAPIBase()}/entities/product-families/${encodeURIComponent(familyId)}/resolve-template`,
      { credentials: 'include' }
    );
    return handle<ResolveTemplateResponse>(res);
  },

  async create(data: ProductFamilyInput): Promise<ProductFamily> {
    const res = await fetch(`${getAPIBase()}/entities/product-families`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify(data),
    });
    return handle<ProductFamily>(res);
  },

  async update(
    id: number,
    data: Partial<ProductFamilyInput>
  ): Promise<ProductFamily> {
    const res = await fetch(
      `${getAPIBase()}/entities/product-families/${id}`,
      {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify(data),
      }
    );
    return handle<ProductFamily>(res);
  },

  async remove(id: number): Promise<{ message: string; id: number }> {
    const res = await fetch(
      `${getAPIBase()}/entities/product-families/${id}`,
      { method: 'DELETE', credentials: 'include' }
    );
    return handle<{ message: string; id: number }>(res);
  },
};