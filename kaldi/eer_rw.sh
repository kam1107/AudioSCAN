. ./cmd.sh
. ./path.sh
set -e
mfccdir=`pwd`/mfcc
vaddir=`pwd`/mfcc

nnet_dir=0007_voxceleb_v2_1a/exp/xvector_nnet_1a
plda_dir=exp/orig_plda
meanshift_plda_dir=exp/meanshift_plda_audioscan_diaseg_corrupted
local_plda_dir=exp/local_plda_audioscan_diaseg_corrupted_soft_scan

rw_test_root=/data/greyheron/not-backed-up/aims/aimsre/xxlu/audio_scan/data/RW_trials
rw_test_trials=data/rw_test/trials


. utils/parse_options.sh

rm -rf data/rw_test
local/make_audioscan_trials.pl $rw_test_root data/rw_test

steps/make_mfcc.sh --write-utt2num-frames true --mfcc-config conf/mfcc.conf --nj 10 --cmd "$train_cmd" \
    data/rw_test exp/make_mfcc $mfccdir
utils/fix_data_dir.sh data/rw_test

sid/compute_vad_decision.sh --nj 10 --cmd "$train_cmd" \
    data/rw_test exp/make_vad $vaddir
utils/fix_data_dir.sh data/rw_test


sid/nnet3/xvector/extract_xvectors.sh --cmd "$train_cmd --mem 4G" --nj 10 \
  $nnet_dir data/rw_test \
  exp/xvectors_rw_test


$train_cmd exp/scores/log/rw_test_scoring.log \
  ivector-plda-scoring --normalize-length=true \
  "ivector-copy-plda --smoothing=0.0 $local_plda_dir/plda - |" \
  "ark:ivector-subtract-global-mean $local_plda_dir/mean.vec scp:exp/xvectors_rw_test/xvector.scp ark:- | transform-vec $local_plda_dir/transform.mat ark:- ark:- | ivector-normalize-length ark:- ark:- |" \
  "ark:ivector-subtract-global-mean $local_plda_dir/mean.vec scp:exp/xvectors_rw_test/xvector.scp ark:- | transform-vec $local_plda_dir/transform.mat ark:- ark:- | ivector-normalize-length ark:- ark:- |" \
  "cat '$rw_test_trials' | cut -d\  --fields=1,2 |" exp/scores_rw_test_trials || exit 1;


eer=`compute-eer <(local/prepare_for_eer.py $rw_test_trials exp/scores_rw_test_trials) 2> /dev/null`
echo "EER: ${eer}%"


