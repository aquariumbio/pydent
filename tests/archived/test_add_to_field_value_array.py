from pydent import models
from marshmallow import pprint

def test_add_field_value_array(session):
    op_type = session.OperationType.where({'name': "Assemble NEB Golden Gate"})[0]
    op = op_type.instance()

    st = session.SampleType.find_by_name("Fragment")

    for sample_name in ['myspecialffrag', 'myfrgfgfag2']:
        s = None
        try:
            s = session.Sample.find_by_name(sample_name)
        except:
            s = models.Sample(
                name=sample_name,
                project='SD2',
                sample_type_id=st.id
            )
            s.connect_to_session(session)
            s.save()
        op.add_to_field_value_array('Inserts', 'input', sample=s)
make