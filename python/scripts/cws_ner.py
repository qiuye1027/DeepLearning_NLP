# -*- coding: UTF-8 -*-
import sys
import argparse
import csv
import xlsxwriter
from dnlp.config import DnnCrfConfig
from dnlp.core.dnn_crf import DnnCrf
from dnlp.core.dnn_crf_emr import DnnCrfEmr
from dnlp.core.word2vec import Word2Vec
from dnlp.utils.evaluation import evaluate_cws, evaluate_ner

EMR_TEST_FILE = '../dnlp/data/emr/emr_test.pickle'


def train_cws():
  data_path = '../dnlp/data/cws/pku_training.pickle'
  config = DnnCrfConfig()
  dnncrf = DnnCrf(config=config, data_path=data_path, nn='lstm')
  dnncrf.fit()


def test_cws():
  sentence = '小明来自南京师范大学'
  sentence = '中国人民决心继承邓小平同志的遗志，继续把建设有中国特色社会主义事业推向前进。'
  model_path = '../dnlp/models/cws32.ckpt'
  config = DnnCrfConfig()
  dnncrf = DnnCrf(config=config, mode='predict', model_path=model_path, nn='lstm')
  res, labels = dnncrf.predict_ll(sentence, return_labels=True)
  print(res)
  evaluate_cws(dnncrf, '../dnlp/data/cws/pku_test.pickle')


def train_emr_cws():
  data_path = '../dnlp/data/emr/emr_cws.pickle'
  config = DnnCrfConfig()
  dnncrf = DnnCrf(config=config, data_path=data_path, nn='lstm', task='cws', remark='emr_cws')
  dnncrf.fit()


def test_emr_cws():
  config = DnnCrfConfig()
  model_path = '../dnlp/models/cws-lstm-emr_cws-20.ckpt'
  dnncrf = DnnCrf(config=config, model_path=model_path, mode='predict', nn='lstm', task='cws', remark='emr_cws')
  sentences = []
  with open('../dnlp/data/emr/emr.txt', encoding='utf-8') as f:
    sentences = [l for l in f.read().splitlines() if l not in ['', None, '\n', '\r', ':']]
  content = []
  for sentence in sentences:
    if len(sentence) <= 2:
      continue
    words = dnncrf.predict_ll(sentence, return_labels=False)
    content.append(' '.join(words))
  with open('../dnlp/data/emr/emr_words.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(content))


def train_emr_ngram(nn):
  data_path = '../dnlp/data/emr/emr_training.pickle'
  config_bi_bigram = DnnCrfConfig(skip_left=1, skip_right=1)
  config_left_bigram = DnnCrfConfig(skip_left=1, skip_right=0)
  config_right_bigram = DnnCrfConfig(skip_left=0, skip_right=1)
  config_unigram = DnnCrfConfig(skip_left=0, skip_right=0)
  mlpcrf_bi_bigram = DnnCrf(config=config_bi_bigram, task='ner', data_path=data_path, nn=nn, remark='bi_bigram')
  mlpcrf_left_bigram = DnnCrf(config=config_left_bigram, task='ner', data_path=data_path, nn=nn,
                              remark='left_bigram')
  mlpcrf_right_bigram = DnnCrf(config=config_right_bigram, task='ner', data_path=data_path, nn=nn,
                               remark='right_bigram')
  mlpcrf_unigram = DnnCrf(config=config_unigram, task='ner', data_path=data_path, nn=nn, remark='unigram')
  mlpcrf_bi_bigram.fit()
  mlpcrf_left_bigram.fit()
  mlpcrf_right_bigram.fit()
  mlpcrf_unigram.fit()


def test_emr_ngram(nn, epoch=40):
  res = []
  bi_bigram_model_path = '../dnlp/models/emr/ner-{0}-bi_bigram-{1}.ckpt'.format(nn, epoch)
  config_bi_bigram = DnnCrfConfig(skip_left=1, skip_right=1)
  mlpcrf_bi_bigram = DnnCrf(model_path=bi_bigram_model_path, config=config_bi_bigram, mode='predict', task='ner',
                            nn=nn)
  res.append(list(evaluate_ner(mlpcrf_bi_bigram, '../dnlp/data/emr/emr_test.pickle')))
  left_bigram_model_path = '../dnlp/models/emr/ner-{0}-left_bigram-{1}.ckpt'.format(nn, epoch)
  config_left_bigram = DnnCrfConfig(skip_left=1, skip_right=0)
  mlpcrf_left_bigram = DnnCrf(model_path=left_bigram_model_path, config=config_left_bigram, mode='predict', task='ner',
                              nn=nn)
  res.append(list(evaluate_ner(mlpcrf_left_bigram, '../dnlp/data/emr/emr_test.pickle')))
  right_bigram_model_path = '../dnlp/models/emr/ner-{0}-right_bigram-{1}.ckpt'.format(nn, epoch)
  config_right_bigram = DnnCrfConfig(skip_left=0, skip_right=1)
  mlpcrf_right_bigram = DnnCrf(model_path=right_bigram_model_path, config=config_right_bigram, mode='predict',
                               task='ner', nn=nn)
  res.append(list(evaluate_ner(mlpcrf_right_bigram, '../dnlp/data/emr/emr_test.pickle')))
  unigram_model_path = '../dnlp/models/emr/ner-{0}-unigram-{1}.ckpt'.format(nn, epoch)
  config_unigram = DnnCrfConfig(skip_left=0, skip_right=0)
  mlpcrf_unigram = DnnCrf(model_path=unigram_model_path, config=config_unigram, mode='predict', task='ner',
                          nn=nn)
  res.append(list(evaluate_ner(mlpcrf_unigram, '../dnlp/data/emr/emr_test.pickle')))
  return res

def train_emr_dropout(nn, skip_left, skip_right):
  data_path = '../dnlp/data/emr/emr_training.pickle'
  lr = 0.05
  config_no_dp = DnnCrfConfig(dropout_rate=0, skip_left=skip_left, skip_right=skip_right,learning_rate=lr)
  mlpcrf_no_dp = DnnCrf(config=config_no_dp, dropout_position='input', task='ner', data_path=data_path, nn=nn,
                        remark='no_dp')
  mlpcrf_no_dp.fit(interval=1)
  config_20_dp = DnnCrfConfig(dropout_rate=0.2, skip_left=skip_left, skip_right=skip_right,learning_rate=lr)
  mlpcrf_20_dp_input = DnnCrf(config=config_20_dp, dropout_position='input', task='ner', data_path=data_path, nn=nn,
                              remark='20_dp_input')
  mlpcrf_20_dp_input.fit(interval=1)
  mlpcrf_20_dp_hidden = DnnCrf(config=config_20_dp, dropout_position='hidden', task='ner', data_path=data_path,
                               nn=nn,
                               remark='20_dp_hidden')
  mlpcrf_20_dp_hidden.fit(interval=1)
  config_50_dp = DnnCrfConfig(dropout_rate=0.5, skip_left=skip_left, skip_right=skip_right,learning_rate=lr)
  mlpcrf_50_dp_input = DnnCrf(config=config_50_dp, dropout_position='input', task='ner', data_path=data_path,
                              nn=nn,
                              remark='50_dp_input')
  mlpcrf_50_dp_input.fit(interval=1)
  mlpcrf_50_dp_hidden = DnnCrf(config=config_50_dp, dropout_position='hidden', task='ner', data_path=data_path,
                               nn=nn,
                               remark='50_dp_hidden')
  mlpcrf_50_dp_hidden.fit(interval=1)


def test_emr_dropout(nn, skip_left, skip_right,epoch=(40,40,40,40)):
  res = []
  config_no_dp = DnnCrfConfig(dropout_rate=0, skip_left=skip_left, skip_right=skip_right)
  config_20_dp = DnnCrfConfig(dropout_rate=0.2, skip_left=skip_left, skip_right=skip_right)
  config_50_dp = DnnCrfConfig(dropout_rate=0.5, skip_left=skip_left, skip_right=skip_right)
  res.append(list(test_single_model(config_no_dp, 'input', nn, 'no_dp')))
  # test_single_model(config, 'hidden', nn, 'no_dp')
  res.append(list(test_single_model(config_20_dp, 'input', nn, '20_dp_input',epoch[0])))
  res.append(list(test_single_model(config_20_dp, 'hidden', nn, '20_dp_hidden',epoch[1])))
  res.append(list(test_single_model(config_50_dp, 'input', nn, '50_dp_input',epoch[2])))
  res.append(list(test_single_model(config_50_dp, 'hidden', nn, '50_dp_hidden',epoch[3])))
  return res

def test_single_model(config, dp, nn, remark,epoch=40):
  model_path = '../dnlp/models/emr/ner-{1}-{0}-40.ckpt'.format(remark, nn)
  dnncrf = DnnCrf(config=config, mode='predict', task='ner', nn=nn, dropout_position=dp, model_path=model_path)
  return evaluate_ner(dnncrf, EMR_TEST_FILE)


def train_emr_old_method():
  data_path = '../dnlp/data/emr/emr_training.pickle'
  config = DnnCrfConfig()
  mlpcrf = DnnCrfEmr(config=config, task='ner', data_path=data_path, nn='rnn')
  mlpcrf.fit(interval=1)


def test_emr_old_method():
  model_path = '../dnlp/models/emr_old/rnn-1.ckpt'
  config = DnnCrfConfig()
  mlpcrf = DnnCrfEmr(config=config, task='ner', mode='predict', model_path=model_path, nn='rnn')

  evaluate_ner(mlpcrf, '../dnlp/data/emr/emr_test.pickle')


def train_emr_random_init():
  data_path = '../dnlp/data/emr/emr_training.pickle'
  interval = 1
  config_mlp = DnnCrfConfig(skip_left=1,skip_right=1,dropout_rate=0.2)
  mlpcrf = DnnCrf(config=config_mlp, dropout_position='hidden',task='ner', data_path=data_path, nn='mlp')
  mlpcrf.fit(interval=interval)
  config_rnn = DnnCrfConfig(skip_left=1, skip_right=0, dropout_rate=0.2)
  rnncrf = DnnCrf(config=config_rnn, task='ner', data_path=data_path, nn='rnn',dropout_position='input')
  rnncrf.fit(interval=interval)
  config_lstm = DnnCrfConfig(skip_left=1, skip_right=1, dropout_rate=0.2)
  lstmcrf = DnnCrf(config=config_lstm, task='ner', data_path=data_path, nn='lstm',dropout_position='input')
  lstmcrf.fit(interval=interval)
  config_bilstm = DnnCrfConfig(skip_left=0, skip_right=1, dropout_rate=0.5)
  bilstmcrf = DnnCrf(config=config_bilstm, task='ner', data_path=data_path, nn='bilstm',dropout_position='input')
  bilstmcrf.fit(interval=interval)
  config_gru = DnnCrfConfig(skip_left=0, skip_right=1, dropout_rate=0.2)
  grulstmcrf = DnnCrf(config=config_gru, task='ner', data_path=data_path, nn='gru',dropout_position='input')
  grulstmcrf.fit(interval=interval)


def test_emr_random_init():
  mlp_model_path = '../dnlp/models/emr/ner-mlp-{0}.ckpt'
  rnn_model_path = '../dnlp/models/emr/ner-rnn-{0}.ckpt'
  lstm_model_path = '../dnlp/models/emr/ner-lstm-{0}.ckpt'
  bilstm_model_path = '../dnlp/models/emr/ner-bilstm-{0}.ckpt'
  gru_model_path = '../dnlp/models/emr/ner-gru-{0}.ckpt'
  config_mlp = DnnCrfConfig(skip_left=1, skip_right=1, dropout_rate=0.2)

  config_rnn = DnnCrfConfig(skip_left=1, skip_right=0, dropout_rate=0.2)

  config_lstm = DnnCrfConfig(skip_left=1, skip_right=1, dropout_rate=0.2)
  config_bilstm = DnnCrfConfig(skip_left=0, skip_right=1, dropout_rate=0.5)

  config_gru = DnnCrfConfig(skip_left=0, skip_right=1, dropout_rate=0.2)

  with open('../dnlp/data/emr/ner_init.csv','w',newline='') as f:
    writer = csv.DictWriter(f,['model_name','p','r','f1'])
    writer.writeheader()
    p,r,f = '0','0','0'
    with open('../dnlp/data/emr/ner_mlp.csv','w',newline='') as ff:
      writer_mlp = csv.DictWriter(ff, ['model_name', 'p', 'r', 'f1'])
      writer_mlp.writeheader()
      for i in range(1,51):
        mlpcrf = DnnCrf(config=config_mlp, task='ner', mode='predict', model_path=mlp_model_path.format(i), nn='mlp')
        p1,r1,f1 = evaluate_ner(mlpcrf, '../dnlp/data/emr/emr_test.pickle')
        writer_mlp.writerow({'model_name':'mlp','p':p1,'r':r1,'f1':f1})
        if float(f1)>float(f):
          p,r,f = p1,r1,f1
    writer.writerow({'model_name':'mlp','p':p,'r':r,'f1':f})
    p,r,f = '0','0','0'
    for i in range(1,51):
      rnncrf = DnnCrf(config=config_rnn, task='ner', mode='predict', model_path=rnn_model_path.format(i), nn='rnn')
      p1, r1, f1 = evaluate_ner(rnncrf, '../dnlp/data/emr/emr_test.pickle')
      if float(f1) > float(f):
        p, r, f = p1, r1, f1
    writer.writerow({'model_name': 'rnn', 'p': p, 'r': r, 'f1': f})
    p,r,f = '0','0','0'
    for i in range(1,51):
      lstmcrf = DnnCrf(config=config_lstm, task='ner', mode='predict', model_path=lstm_model_path.format(i), nn='lstm')
      p1, r1, f1 = evaluate_ner(lstmcrf, '../dnlp/data/emr/emr_test.pickle')
      if float(f1) > float(f):
        p, r, f = p1, r1, f1
    writer.writerow({'model_name': 'lstm', 'p': p, 'r': r, 'f1': f})
    p, r, f = '0', '0', '0'
    for i in range(1,51):
      bilstmcrf = DnnCrf(config=config_bilstm, task='ner', mode='predict', model_path=bilstm_model_path.format(i),
                         nn='bilstm')
      p1, r1, f1 = evaluate_ner(bilstmcrf, '../dnlp/data/emr/emr_test.pickle')
      if float(f1) > float(f):
        p, r, f = p1, r1, f1
    writer.writerow({'model_name': 'bilstm', 'p': p, 'r': r, 'f1': f})
    p,r,f = '0','0','0'
    for i in range(1,51):
      grucrf = DnnCrf(config=config_gru, task='ner', mode='predict', model_path=gru_model_path.format(i), nn='gru')
      p1, r1, f1 = evaluate_ner(grucrf, '../dnlp/data/emr/emr_test.pickle')
      if float(f1) > float(f):
        p, r, f = p1, r1, f1
    writer.writerow({'model_name': 'gru', 'p': p, 'r': r, 'f1': f})
def fmt(n):
  return str('{0:.2f}').format(n*100)
def train_emr_with_embeddings():
  data_path = '../dnlp/data/emr/emr_training.pickle'
  embedding_path = '../dnlp/data/emr/emr_skip_gram.npy'
  config = DnnCrfConfig()
  mlpcrf = DnnCrf(config=config, task='ner', data_path=data_path, nn='mlp', embedding_path=embedding_path)
  # mlpcrf.fit()
  rnncrf = DnnCrf(config=config, task='ner', data_path=data_path, nn='rnn', embedding_path=embedding_path)
  # rnncrf.fit()
  lstmcrf = DnnCrf(config=config, task='ner', data_path=data_path, nn='lstm', embedding_path=embedding_path)
  # lstmcrf.fit()
  bilstmcrf = DnnCrf(config=config, task='ner', data_path=data_path, nn='bilstm', embedding_path=embedding_path)
  bilstmcrf.fit()
  grulstmcrf = DnnCrf(config=config, task='ner', data_path=data_path, nn='gru', embedding_path=embedding_path)
  grulstmcrf.fit()


def test_emr_with_embeddings():
  config = DnnCrfConfig()
  embedding_path = '../dnlp/data/emr/emr_skip_gram.npy'
  mlp_model_path = '../dnlp/models/emr/ner-mlp-embedding-50.ckpt'
  rnn_model_path = '../dnlp/models/emr/ner-rnn-embedding-50.ckpt'
  lstm_model_path = '../dnlp/models/emr/ner-lstm-embedding-50.ckpt'
  bilstm_model_path = '../dnlp/models/emr/ner-bilstm-embedding-50.ckpt'
  gru_model_path = '../dnlp/models/emr/ner-gru-embedding-50.ckpt'
  mlpcrf = DnnCrf(config=config, task='ner', mode='predict', model_path=mlp_model_path, nn='mlp',
                  embedding_path=embedding_path)
  rnncrf = DnnCrf(config=config, task='ner', mode='predict', model_path=rnn_model_path, nn='rnn',
                  embedding_path=embedding_path)
  lstmcrf = DnnCrf(config=config, task='ner', mode='predict', model_path=lstm_model_path, nn='lstm',
                   embedding_path=embedding_path)
  bilstmcrf = DnnCrf(config=config, task='ner', mode='predict', model_path=bilstm_model_path, nn='bilstm',
                     embedding_path=embedding_path)
  grucrf = DnnCrf(config=config, task='ner', mode='predict', model_path=gru_model_path, nn='gru',
                  embedding_path=embedding_path)
  evaluate_ner(mlpcrf, '../dnlp/data/emr/emr_test.pickle')
  evaluate_ner(rnncrf, '../dnlp/data/emr/emr_test.pickle')
  evaluate_ner(lstmcrf, '../dnlp/data/emr/emr_test.pickle')
  evaluate_ner(bilstmcrf, '../dnlp/data/emr/emr_test.pickle')
  evaluate_ner(grucrf, '../dnlp/data/emr/emr_test.pickle')

def evaluate_hyperparameter():
  workbook = xlsxwriter.Workbook('../dnlp/data/emr/ner_ngram.xlsx')
  worksheet_mlp = workbook.add_worksheet(name='mlp')

  res = test_emr_ngram('mlp')
  worksheet_mlp.write_row(1,0,res[0])
  worksheet_mlp.write_row(2,0,res[1])
  worksheet_mlp.write_row(3, 0, res[2])
  worksheet_mlp.write_row(4, 0, res[3])
  res = test_emr_ngram('rnn')
  worksheet_rnn = workbook.add_worksheet(name='rnn')
  worksheet_rnn.write_row(1, 0, res[0])
  worksheet_rnn.write_row(2, 0, res[1])
  worksheet_rnn.write_row(3, 0, res[2])
  worksheet_rnn.write_row(4, 0, res[3])
  res = test_emr_ngram('lstm')
  worksheet_lstm = workbook.add_worksheet(name='lstm')
  worksheet_lstm.write_row(1, 0, res[0])
  worksheet_lstm.write_row(2, 0, res[1])
  worksheet_lstm.write_row(3, 0, res[2])
  worksheet_lstm.write_row(4, 0, res[3])
  res = test_emr_ngram('bilstm')
  worksheet_bilstm = workbook.add_worksheet(name='bilstm')
  worksheet_bilstm.write_row(1, 0, res[0])
  worksheet_bilstm.write_row(2, 0, res[1])
  worksheet_bilstm.write_row(3, 0, res[2])
  worksheet_bilstm.write_row(4, 0, res[3])
  res = test_emr_ngram('gru',epoch=30)
  worksheet_gru = workbook.add_worksheet(name='gru')
  worksheet_gru.write_row(1, 0, res[0])
  worksheet_gru.write_row(2, 0, res[1])
  worksheet_gru.write_row(3, 0, res[2])
  worksheet_gru.write_row(4, 0, res[3])
  workbook.close()
  workbook_dp = xlsxwriter.Workbook('../dnlp/data/emr/ner_dropout.xlsx')
  res = test_emr_dropout('mlp', 1, 1,(10,1,10,10))
  worksheet_mlp = workbook_dp.add_worksheet('mlp')
  worksheet_mlp.write_row(1,0,res[0])
  worksheet_mlp.write_row(2, 0, res[1])
  worksheet_mlp.write_row(3, 0, res[2])
  worksheet_mlp.write_row(4, 0, res[3])
  worksheet_mlp.write_row(5, 0, res[4])
  res = test_emr_dropout('rnn', 1, 0)
  worksheet_rnn = workbook_dp.add_worksheet('rnn')
  worksheet_rnn.write_row(1, 0, res[0])
  worksheet_rnn.write_row(2, 0, res[1])
  worksheet_rnn.write_row(3, 0, res[2])
  worksheet_rnn.write_row(4, 0, res[3])
  worksheet_rnn.write_row(5, 0, res[4])
  res = test_emr_dropout('lstm', 1, 1)
  worksheet_lstm = workbook_dp.add_worksheet('lstm')
  worksheet_lstm.write_row(1, 0, res[0])
  worksheet_lstm.write_row(2, 0, res[1])
  worksheet_lstm.write_row(3, 0, res[2])
  worksheet_lstm.write_row(4, 0, res[3])
  worksheet_lstm.write_row(5, 0, res[4])
  res = test_emr_dropout('bilstm', 0, 1)
  worksheet_bilstm = workbook_dp.add_worksheet('bilstm')
  worksheet_bilstm.write_row(1, 0, res[0])
  worksheet_bilstm.write_row(2, 0, res[1])
  worksheet_bilstm.write_row(3, 0, res[2])
  worksheet_bilstm.write_row(4, 0, res[3])
  worksheet_bilstm.write_row(5, 0, res[4])
  res =  test_emr_dropout('gru', 0, 1)
  worksheet_gru = workbook_dp.add_worksheet('gru')
  worksheet_gru.write_row(1, 0, res[0])
  worksheet_gru.write_row(2, 0, res[1])
  worksheet_gru.write_row(3, 0, res[2])
  worksheet_gru.write_row(4, 0, res[3])
  worksheet_gru.write_row(5, 0, res[4])
  workbook_dp.close()


def train_emr_skipgram():
  base_folder = '../dnlp/data/emr/'
  skipgram = Word2Vec(base_folder + 'emr_skip_gram.pickle', base_folder + 'emr_skip_gram')
  skipgram.train()


def train_emr_word_skipgram():
  base_folder = '../dnlp/data/emr/'
  skipgram = Word2Vec(base_folder + 'emr_word_skip_gram.pickle', base_folder + 'emr_word_skip_gram', embed_size=300)
  skipgram.train()
  light_skipgram = Word2Vec(base_folder + 'emr_word_light_skip_gram.pickle', base_folder + 'emr_word_light_skip_gram',
                            embed_size=300)
  light_skipgram.train()


def train_emr_word_cbow():
  base_folder = '../dnlp/data/emr/'
  cbow = Word2Vec(base_folder + 'emr_word_cbow.pickle', base_folder + 'emr_word_cbow', mode='cbow', embed_size=300,
                  window_size=2)
  cbow.train()
  light_cbow = Word2Vec(base_folder + 'emr_word_light_cbow.pickle', base_folder + 'emr_word_light_cbow', mode='cbow',
                        embed_size=300, window_size=2)
  light_cbow.train()


def export_cws(data, filename):
  fieldnames = ['model', 'p', 'r', 'f1']
  with open(filename, 'w') as f:
    writer = csv.DictWriter(f, fieldnames)
    writer.writeheader()
    for line in data:
      writer.writerow(line)


if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  parser.add_argument('-t', '--t', dest='train', action='store_true', default=False)
  parser.add_argument('-p', '--p', dest='predict', action='store_true', default=False)
  parser.add_argument('-c', '--c', dest='cws', action='store_true', default=False)
  parser.add_argument('-e', '--e', dest='emr', action='store_true', default=False)
  args = parser.parse_args(sys.argv[1:])
  train = args.train
  predict = args.predict
  if train and predict:
    print('can\'t train and predict at same time')
    exit(1)
  elif not train and not predict:
    print('don\'t enter mode')
    exit(1)

  if train:
    if args.cws:
      train_cws()
    elif args.emr:
      # train_emr_old_method()
      # train_emr_cws()
      # train_emr_word_skipgram()
      train_emr_word_cbow()
      # train_emr_with_embeddings()
      # train_emr_ngram('mlp')
      # train_emr_ngram('rnn')
      # train_emr_ngram('bilstm')
      # train_emr_ngram('gru')
      # train_emr_dropout('mlp',1,1)
      # train_emr_dropout('rnn',1,0)
      # train_emr_dropout('lstm',1,1)
      # train_emr_dropout('bilstm',0,1)
      # train_emr_dropout('gru', 0, 1)
      # train_emr_random_init()
      # train_emr_skipgram()
  else:
    if args.cws:
      test_cws()
    elif args.emr:
      # test_emr_cws()
      # test_emr_old_method()
      test_emr_random_init()
      # evaluate_hyperparameter()
      # print('embedding')
      # test_emr_with_embeddings()
