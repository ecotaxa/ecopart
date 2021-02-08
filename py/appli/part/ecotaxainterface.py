import psycopg2.extras
from appli import db, database, DecodeEqualList
from appli.part import database as partdatabase


def GetObjectsForTaxoHistoCompute(prj: partdatabase.part_projects, eco_sampleid: int):
    eco_prj = db.session.query(database.Projects).filter_by(projid=prj.projid).first()
    if eco_prj is None:
        raise Exception("GenerateTaxonomyHistogram: Ecotaxa project %d missing" % prj.projid)
    objmap = DecodeEqualList(eco_prj.mappingobj)
    areacol = None
    for k, v in objmap.items():
        if v.lower() == 'area':
            areacol = k
            break
    if areacol is None:
        raise Exception("GenerateTaxonomyHistogram: esd attribute required in Ecotaxa project %d" % prj.projid)
    lst_taxo_det = database.GetAll("""
                    select classif_id,depth_min depth,objdate+objtime objdatetime,{areacol} areacol                           
                    from objects
                    WHERE sampleid={sampleid} and classif_id is not NULL and depth_min is not NULL 
                    and {areacol} is not NULL and classif_qual='V'
                    """.format(sampleid=eco_sampleid, areacol=areacol), None, False, psycopg2.extras.RealDictCursor)
    return lst_taxo_det


def GetObjectsForRawExport(psampleid: int,
                           excludenotliving: bool,
                           includenotvalidated: bool) -> list:
    sql = """select of.*
        ,t0.display_name as "name", classif_qual ,ps.psampleid                        
        ,((oh.depth_min+oh.depth_max)/2) as depth_including_offset,objid
        ,concat(t14.name||'>',t13.name||'>',t12.name||'>',t11.name||'>',t10.name||'>',t9.name||'>'
                ,t8.name||'>',t7.name||'>',t6.name||'>',t5.name||'>',t4.name||'>',t3.name||'>'
                ,t2.name||'>',t1.name||'>',t0.name) taxo_hierarchy
      from part_samples ps
      join obj_head oh on ps.sampleid=oh.sampleid 
      join obj_field of on of.objfid=oh.objid                      
        join taxonomy t0 on oh.classif_id=t0.id
        left join taxonomy t1 on t0.parent_id=t1.id
        left join taxonomy t2 on t1.parent_id=t2.id
        left join taxonomy t3 on t2.parent_id=t3.id
        left join taxonomy t4 on t3.parent_id=t4.id
        left join taxonomy t5 on t4.parent_id=t5.id
        left join taxonomy t6 on t5.parent_id=t6.id
        left join taxonomy t7 on t6.parent_id=t7.id
        left join taxonomy t8 on t7.parent_id=t8.id
        left join taxonomy t9 on t8.parent_id=t9.id
        left join taxonomy t10 on t9.parent_id=t10.id
        left join taxonomy t11 on t10.parent_id=t11.id
        left join taxonomy t12 on t11.parent_id=t12.id
        left join taxonomy t13 on t12.parent_id=t13.id
        left join taxonomy t14 on t13.parent_id=t14.id                                           
      where ps.psampleid=%s  """
    if excludenotliving:
        sql += """ and coalesce(t14.name,t13.name,t12.name,t11.name,t10.name,t9.name,t8.name,t7.name
                        ,t6.name,t5.name,t4.name,t3.name,t2.name,t1.name,t0.name)!='not-living' """
    if includenotvalidated == False:
        sql += " and oh.classif_qual='V' "
    sql += "  order by of.orig_id,oh.objid "
    res = database.GetAll(sql, (psampleid,),cursor_factory=psycopg2.extras.RealDictCursor)
    return res
