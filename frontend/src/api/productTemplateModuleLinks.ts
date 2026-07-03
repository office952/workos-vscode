import { client } from "@/lib/api";

export interface ProductTemplateModuleLinkEntity {
  id: number;
  parent_template_id: number;
  parent_template_code: string;
  module_template_id: number;
  module_template_code: string;
  relation_type: string;
  trigger_field: string;
  trigger_value_json: string;
  input_mapping_json: string;
  default_values_json: string | null;
  pricing_mode: string;
  execution_mode: string;
  active: boolean;
  notes: string | null;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface ProductTemplateModuleLinkListResponse {
  items: ProductTemplateModuleLinkEntity[];
  total: number;
  skip: number;
  limit: number;
}

const ENTITY_NAME = "product-template-module-links";
const entityClient = client.entities[ENTITY_NAME];

export const productTemplateModuleLinksApi = {
  list: async (opts: {
    skip?: number;
    limit?: number;
    query?: Record<string, unknown>;
    sort?: string;
  } = {}): Promise<ProductTemplateModuleLinkListResponse> => {
    const res = await entityClient.query({
      query: opts.query,
      sort: opts.sort ?? "-updated_at",
      limit: opts.limit ?? 500,
      skip: opts.skip ?? 0,
    });
    const data = res?.data;
    if (data && Array.isArray(data.items)) return data as ProductTemplateModuleLinkListResponse;
    if (Array.isArray(data)) return { items: data, total: data.length, skip: 0, limit: data.length };
    if (data?.data && Array.isArray(data.data.items)) return data.data as ProductTemplateModuleLinkListResponse;
    return { items: [], total: 0, skip: 0, limit: 0 };
  },
};
