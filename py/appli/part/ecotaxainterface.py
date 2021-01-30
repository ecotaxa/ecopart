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
