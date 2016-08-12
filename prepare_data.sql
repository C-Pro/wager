create or replace function skills_to_bits(a int[]) returns bit(1024) as
$$
declare
    v bit(1024) := 0::bit(1024);
    v_shift int;
    i int;
begin
    foreach i in array a loop
        v_shift := bit-1 from top_skills where skill_id = i;
        if v_shift is not null then
            v := v | (1::bit(1024) << v_shift);
        end if;
    end loop;
    return v;
end;
$$ language plpgsql;

create table t_skills as select s.skill_id,s.name,count(*) from kb.skills s join vac.vacancies_search vs on (vs.skill_ids @> array[s.skill_id]) group by s.skill_id,s.name order by count(*) desc limit 1024;
create table top_skills as select row_number() over (order by count) as bit, ts.* from t_skills ts;
create unique index si on top_skills (skill_id);
create unique index sbi on top_skills (bit);

create table t_jobs as select j.job_id,j.name,count(*) from kb.jobs j join vac.vacancies_search vs on (vs.job_id = j.job_id) group by j.job_id, j.name order by count(*) desc limit 128;
create table top_jobs as select row_number() over (order by count) as id, tj.* from t_jobs tj;


create table t_areas as select a.area_id,a.name,count(*) from kb.areas a join vac.vacancies_search vs on (vs.area_id = a.area_id) group by a.area_id, a.name order by count(*) desc limit 128;
create table top_areas as select row_number() over (order by count) as id, ta.* from t_areas ta;

create table bitlearn as select ta.id as top_area_id,
                                tj.id as top_job_id,
                                skills_to_bits(skill_ids), 
                                wage,
                                row_number() over (order by random())
from vac.vacancies_search vs 
join top_areas ta on (vs.area_id = ta.area_id)
join top_jobs tj on (vs.job_id = tj.job_id)
where vs.wage between 10000 and 200000 and
      array_length(skill_ids,1)>0;

