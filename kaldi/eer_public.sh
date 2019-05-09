. ./cmd.sh
. ./path.sh
set -e
mfccdir=`pwd`/mfcc
vaddir=`pwd`/mfcc

nnet_dir=0007_voxceleb_v2_1a/exp/xvector_nnet_1a
plda_dir=exp/orig_plda
meanshift_plda_dir=exp/meanshift_plda_50vs20_PLM_100
local_plda_dir=exp/local_plda_50vs20_PLM_soft_scan_100
mix_plda_dir=exp/mix_plda_50vs20_PLM_soft_scan_100

synth_test_root=/data/greyheron/not-backed-up/aims/aimsre/xxlu/audio_scan/data/PLM/synth_test
synth_test_trials=data/synth_test/trials


. utils/parse_options.sh

rm -rf data/synth_test
local/make_synth_trials.pl $synth_test_root data/synth_test

steps/make_mfcc.sh --write-utt2num-frames true --mfcc-config conf/mfcc.conf --nj 50 --cmd "$train_cmd" \
    data/synth_test exp/make_mfcc $mfccdir
utils/fix_data_dir.sh data/synth_test

sid/compute_vad_decision.sh --nj 50 --cmd "$train_cmd" \
    data/synth_test exp/make_vad $vaddir
utils/fix_data_dir.sh data/synth_test


sid/nnet3/xvector/extract_xvectors.sh --cmd "$train_cmd --mem 4G" --nj 50 \
  $nnet_dir data/synth_test \
  exp/xvectors_synth_test


$train_cmd exp/scores/log/synth_test_scoring.log \
  ivector-plda-scoring --normalize-length=true \
  "ivector-copy-plda --smoothing=0.0 $mix_plda_dir/plda - |" \
  "ark:ivector-subtract-global-mean $mix_plda_dir/mean.vec scp:exp/xvectors_synth_test/xvector.scp ark:- | transform-vec $mix_plda_dir/transform.mat ark:- ark:- | ivector-normalize-length ark:- ark:- |" \
  "ark:ivector-subtract-global-mean $mix_plda_dir/mean.vec scp:exp/xvectors_synth_test/xvector.scp ark:- | transform-vec $mix_plda_dir/transform.mat ark:- ark:- | ivector-normalize-length ark:- ark:- |" \
  "cat '$synth_test_trials' | cut -d\  --fields=1,2 |" exp/scores_synth_test_trials || exit 1;


eer=`compute-eer <(local/prepare_for_eer.py $synth_test_trials exp/scores_synth_test_trials) 2> /dev/null`
echo "EER: ${eer}%"


