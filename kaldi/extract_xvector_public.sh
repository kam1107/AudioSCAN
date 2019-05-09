. ./cmd.sh
. ./path.sh
set -e
mfccdir=`pwd`/mfcc
vaddir=`pwd`/mfcc

synth_list_root=/data/greyheron/not-backed-up/aims/aimsre/xxlu/audio_scan/data/PLM/50vs20_PLM_100
synth_trials=data/50vs20_PLM_100/trials
# path to xvector extractor model
nnet_dir=0007_voxceleb_v2_1a/exp/xvector_nnet_1a
# path to PLDA model
plda_dir=exp/xvectors_plda_v1

. utils/parse_options.sh

local/make_synth_list.pl $synth_list_root data/50vs20_PLM_100

steps/make_mfcc.sh --write-utt2num-frames true --mfcc-config conf/mfcc.conf --nj 40 --cmd "$train_cmd" \
    data/50vs20_PLM_100 exp/make_mfcc $mfccdir
utils/fix_data_dir.sh data/50vs20_PLM_100

sid/compute_vad_decision.sh --nj 40 --cmd "$train_cmd" \
    data/50vs20_PLM_100 exp/make_vad $vaddir
utils/fix_data_dir.sh data/50vs20_PLM_100


sid/nnet3/xvector/extract_xvectors.sh --cmd "$train_cmd --mem 4G" --nj 40 \
    $nnet_dir data/50vs20_PLM_100 exp/xvectors_50vs20_PLM_100

$train_cmd exp/scores/log/50vs20_PLM_100_scoring.log \
    ivector-plda-scoring --normalize-length=true \
    "ivector-copy-plda --smoothing=0.0 $plda_dir/plda - |" \
    "ark:ivector-subtract-global-mean $plda_dir/mean.vec scp:exp/xvectors_50vs20_PLM_100/xvector.scp ark:- | transform-vec $plda_dir/transform.mat ark:- ark:- | ivector-normalize-length ark:- ark:- |" \
    "ark:ivector-subtract-global-mean $plda_dir/mean.vec scp:exp/xvectors_50vs20_PLM_100/xvector.scp ark:- | transform-vec $plda_dir/transform.mat ark:- ark:- | ivector-normalize-length ark:- ark:- |" \
    "cat $synth_trials | cut -d\  --fields=1,2 |" exp/scores_50vs20_PLM_100 || exit 1;


python3 make_XVEC.py

