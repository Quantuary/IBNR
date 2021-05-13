--Created on Mon Feb 25 22:41:40 2020
--@author: mleong
-- added risk group category

select 
  ACCOUNTING_MONTH_DATE
  ,ACCIDENT_MONTH_DATE
  
  ,PRODUCT_CODE
  ,CLAIM_CATEGORY
  ,PRODUCT_CODE_CLAIM
  ,CLAIM_CATEGORY_RESERVING
  ,CLIENT_NAME
  ,PRODUCT_GROUP
  ,case when PRODUCT_CODE = 119 then
        (case when CLIENT_NAME='ANZAU'                             then '119_G1'
              when CLIENT_NAME in ('BOM', 'BOSA', 'STGEO', 'WPAC') then '119_G2'
              when CLIENT_NAME = 'NAB'                             then '119_G3'
              when CLIENT_NAME='CITIGROUP'                         then '119_G4'
                                                                  else '119_G5' end
          )
      when product_code in (111,116) then
         (case when CLIENT_NAME='ALLIANZ'                           then '116_G1'
               when CLIENT_NAME='WORLDCARE'                         then '116_G2'
               when CLIENT_NAME='ONLINE TVL'                        then '116_G3'
               when product_group in ('E-Comm','Cancellation')      then '116_G4'
                                                                  else '116_G5' end
          ) 
    else  ''  end as risk_group
  
  
  ,CLAIM_PAID_EX_GST_D
  
  from actuary.dar_t_ibnr_triangles
  
  where ACCIDENT_MONTH_DATE > to_date('31/12/2015', 'dd/mm/yyyy')
  and ACCOUNTING_MONTH_DATE > to_date('31/12/2015', 'dd/mm/yyyy')
  and ACCOUNTING_MONTH_DATE <= to_date('30/04/2021', 'dd/mm/yyyy')
  and ACCIDENT_MONTH_DATE <= to_date('30/04/2021', 'dd/mm/yyyy')
  
--  union all
--  (select 
--    trunc(init_claim_serviced_month, 'MM') as ACCIDENT_MONTH_DATE, 
--    trunc(CLAIM_PAID_MONTH, 'MM') as ACCOUNTING_MONTH_DATE,
--    352 as PRODUCT_CODE,
--    (case when cl_paid > 50000 then 'Large Loss' else 'Working Loss' end) as CLAIM_CATEGORY,
--    null as PRODUCT_CODE_CLAIM,
--    origin as CLAIM_CATEGORY_RESERVING,
--    'blank' as CLIENT_NAME,
--    'blank' as PRODUCT_GROUP,
--    'blank' as risk_group,
--    sum(cl_paid) as CLAIM_PAID_EX_GST_D
--    from rep_ov_claims_raw_new
--  
--  where init_claim_serviced_month <= to_date('31/01/2021', 'dd/mm/yyyy')
--  and CLAIM_PAID_MONTH <= to_date('31/01/2021', 'dd/mm/yyyy')
--  
--  group by 
--  trunc(init_claim_serviced_month, 'MM'),
--  trunc(CLAIM_PAID_MONTH, 'MM'),
--  origin, case when cl_paid > 50000 then 'Large Loss' else 'Working Loss' end)