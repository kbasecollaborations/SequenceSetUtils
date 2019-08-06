from datetime import datetime
import os
from installed_clients.DataFileUtilClient import DataFileUtil


class FastaUtil:
    def __init__(self, config):
        self.dfu = DataFileUtil(os.environ['SDK_CALLBACK_URL'])
        self.scratch = config['scratch']

    def SS2Fasta(self, params):
        seq_set = self.dfu.get_objects({'object_refs': [params['SS_ref']]})['data'][0]['data']

        output_fasta_file = os.path.join(self.scratch, str(seq_set['sequence_set_id'])+'.fasta')

        with open(output_fasta_file, 'w') as f:
            for s in seq_set['sequences']:
                f.write('> ' + s['sequence_id'] + '\n')
                f.write(s['sequence']+'\n\n')

            f.close()

        return output_fasta_file

    def openFasta(self, fastalocation):
        # TODO: check other file methods
        if 'path' not in fastalocation or fastalocation['path'] == '':
            # 'shock_id' and 'ftp_url' possible as well
            raise FileNotFoundError('No file path in fasta path input')

        self.fasta = open(fastalocation['path'], 'r')
        self.sequenceset = {}


    def buildSeqSet(self, params):
        self.openFasta(params['file'])

        if 'seqsetname' not in params or params['seqsetname'] is '':
            self.objname = 'SequenceSet' + 'SequenceSet' + \
                      str(int((datetime.utcnow() - datetime.utcfromtimestamp(0)).total_seconds() * 1000))
        else:
            self.objname = params['seqsetname']

        self.sequenceset['sequence_set_id'] = self.objname
        self.sequenceset['description'] = 'SequenceSet built from fasta'
        self.sequenceset['sequences'] = []

        sequence = {}
        for line in self.fasta:
            if '>' in line:
                sequence = {}
                sequence['sequence_id'] = line.replace('\n', '').replace('>', '')
                sequence['description'] = line.replace('\n', '').replace('>', '')
                sequence['source'] = {'location': [], 'assembly_id': ''}
            else:
                sequence['sequence'] = line.replace('\n', '')
                self.sequenceset['sequences'].append(sequence)

        return self.sequenceset

    def saveSeqSet(self, params):
        if self.objname is '':
            raise ValueError('SequenceSet object name not set.')

        if self.sequenceset == {}:
            raise ValueError('SequenceSet instance is empty')

        objinfo = self.dfu.save_objects({
            'id': self.dfu.ws_name_to_id(params['ws_name']),
            'objects': [{
                'type': 'KBaseSequences.SequenceSet',
                'data': self.sequenceset,
                'name': self.objname
            }]
        })[0]

        return str(objinfo[6]) + '/' + str(objinfo[0]) + '/' + str(objinfo[4])
