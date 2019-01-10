. ./cmd.sh
. ./path.sh
set -e
mfccdir=`pwd`/mfcc
vaddir=`pwd`/mfcc

nnet_dir=0007_voxceleb_v2_1a/exp/xvector_nnet_1a
plda_dir=exp/xvectors_plda_v1

synth_trials_root=/data/greyheron/not-backed-up/aims/aimsre/xxlu/audio_scan/data/RW_trials
synth_trials_trials=data/synth_trials/trials


. utils/parse_options.sh

rm -rf data/synth_trials
local/make_audioscan_trials.pl $synth_trials_root data/synth_trials

steps/make_mfcc.sh --write-utt2num-frames true --mfcc-config conf/mfcc.conf --nj 10 --cmd "$train_cmd" \
    data/synth_trials exp/make_mfcc $mfccdir
utils/fix_data_dir.sh data/synth_trials

sid/compute_vad_decision.sh --nj 10 --cmd "$train_cmd" \
    data/synth_trials exp/make_vad $vaddir
utils/fix_data_dir.sh data/synth_trials


sid/nnet3/xvector/extract_xvectors.sh --cmd "$train_cmd --mem 4G" --nj 10 \
  $nnet_dir data/synth_trials \
  exp/xvectors_synth_trials


$train_cmd exp/scores/log/synth_trials_scoring.log \
  ivector-plda-scoring --normalize-length=true \
  "ivector-copy-plda --smoothing=0.0 $plda_dir/plda - |" \
  "ark:ivector-subtract-global-mean $plda_dir/mean.vec scp:exp/xvectors_synth_trials/xvector.scp ark:- | transform-vec $plda_dir/transform.mat ark:- ark:- | ivector-normalize-length ark:- ark:- |" \
  "ark:ivector-subtract-global-mean $plda_dir/mean.vec scp:exp/xvectors_synth_trials/xvector.scp ark:- | transform-vec $plda_dir/transform.mat ark:- ark:- | ivector-normalize-length ark:- ark:- |" \
  "cat '$synth_trials_trials' | cut -d\  --fields=1,2 |" exp/scores_synth_trials_trials || exit 1;


eer=`compute-eer <(local/prepare_for_eer.py $synth_trials_trials exp/scores_synth_trials_trials) 2> /dev/null`
echo "EER: ${eer}%"


