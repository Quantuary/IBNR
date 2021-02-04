--Created on Mon Dec 14 22:41:40 2020
--@author: mleong

select 
  trunc(init_claim_serviced_month, 'MM') as ACCIDENT_MONTH_DATE, 
  trunc(CLAIM_PAID_MONTH, 'MM') as ACCOUNTING_MONTH_DATE,
  352 as PRODUCT_CODE,
  (case when cl_paid > 50000 then 'Large Loss' else 'Working Loss' end) as CLAIM_CATEGORY,
  null as PRODUCT_CODE_CLAIM,
  origin as CLAIM_CATEGORY_RESERVING,
  'blank' as CLIENT_NAME,
  'blank' as PRODUCT_GROUP,
  sum(cl_paid) as CLAIM_PAID_EX_GST_D
  from rep_ov_claims_raw_new

where init_claim_serviced_month <= to_date('31/10/2020', 'dd/mm/yyyy')
and CLAIM_PAID_MONTH <= to_date('31/10/2020', 'dd/mm/yyyy')

group by 
trunc(init_claim_serviced_month, 'MM'),
trunc(CLAIM_PAID_MONTH, 'MM'),
origin, case when cl_paid > 50000 then 'Large Loss' else 'Working Loss' end

union all

select 
ACCOUNTING_MONTH_DATE,
ACCIDENT_MONTH_DATE,

PRODUCT_CODE,
CLAIM_CATEGORY,
PRODUCT_CODE_CLAIM,
CLAIM_CATEGORY_RESERVING,
CLIENT_NAME,
PRODUCT_GROUP,

CLAIM_PAID_EX_GST_D

from actuary.dar_t_ibnr_triangles

where ACCIDENT_MONTH_DATE > to_date('31/12/2015', 'dd/mm/yyyy')
and ACCOUNTING_MONTH_DATE > to_date('31/12/2015', 'dd/mm/yyyy')
and ACCOUNTING_MONTH_DATE <= to_date('31/10/2020', 'dd/mm/yyyy')
and ACCIDENT_MONTH_DATE <= to_date('31/10/2020', 'dd/mm/yyyy')
